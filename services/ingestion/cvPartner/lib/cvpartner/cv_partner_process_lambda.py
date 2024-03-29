from dataplattform.common.handlers.process import PersonDataProcessHandler
from dataplattform.common.repositories.person_repository import PersonIdentifierType
from typing import Dict
import pandas as pd
import numpy as np

handler = PersonDataProcessHandler(PersonIdentifierType.EMAIL)


@handler.process(partitions={}, overwrite=True, overwrite_all_versions=True,
                 person_data_tables=['cv_partner_employees'])
def process(data, events) -> Dict[str, pd.DataFrame]:
    def make_dataframe(d):
        d = d.json()
        payload = d['data']
        df = pd.json_normalize(payload)
        return df

    def none_to_empty_str(tmp_str):
        if tmp_str is None:
            return ''
        else:
            return str(tmp_str)

    """
    Workaround for known pandas issue with conversion to int in
    the presence of nullable integers.
    """

    def column_type_to_int(col):
        col = pd.to_numeric(col, errors='coerce')
        col = col.fillna(value=0)
        col = col.astype(dtype='int32')
        return col

    employee_table = [
        'user_id',
        'default_cv_id',
        'cv_link',
        'cv.navn',
        'cv.email',
        'cv.telefon',
        'cv.born_year',
        'cv.nationality.int',
        'cv.place_of_residence.int',
        'cv.twitter',
        'cv.title.no',
        'image_key'
    ]

    df = pd.concat([make_dataframe(d) for d in data])
    employee_df = df[employee_table].copy()
    employee_df.rename(columns={
        'cv_link': 'link',
        'cv.navn': 'navn',
        'cv.email': 'email',
        'cv.telefon': 'telefon',
        'cv.born_year': 'born_year',
        'cv.nationality.int': 'nationality',
        'cv.place_of_residence.int': 'place_of_residence',
        'cv.twitter': 'twitter',
        'cv.title.no': 'title'}, inplace=True)
    employee_df['born_year'] = column_type_to_int(employee_df['born_year'])
    employee_df = employee_df.fillna("")

    """
    Transforms:
        {
            elem_tag: "list1[0]",
            "cv": {
                "topic_list": [
                    {
                        "topic_elem": "val0"
                    },
                    {
                        "topic_elem": "val1"
                    },
                ]
            }
        },
        {
            elem_tag: "list1[1]",
            "cv": {
                "topic_list": [
                    {
                        "topic_elem": "val2"
                    },
                    {
                        "topic_elem": "val3"
                    },
                ]
            }
        },
    to dataframe:

    |elem_tag topic_elem|
    list1[0]  val0
    list1[0]  val1
    list1[1]  val2
    list1[1]  val3

    @param: elem_tag
    @param: list1
    @param: topic_list
    """

    def create_from_topic(elem_tag, list1, topic_list):
        def create_df_for_each_elem(elem_tag, list1_elem, topic):
            if not isinstance(topic, list):
                return None
            if not topic:
                return None
            return pd.DataFrame.from_records(np.array([{elem_tag: list1_elem, **x} for x in topic]))

        tmp_df_list = [create_df_for_each_elem(
            elem_tag, l_var, t) for l_var, t in zip(list1, topic_list)]
        if np.sum(x is not None for x in tmp_df_list) == 0:
            return None
        return pd.concat([create_df_for_each_elem(elem_tag,
                                                  list1[indx], topic_list[indx]) for indx in range(topic_list.size)],
                         ignore_index=True)

    """
    If a sub category of the cv structure has a dictonary as a value, it must be normalized to only
    constitute one value in the final dataframe. The values are assumed given as
    ....
    sub_category : { tag1: val1, tag2: val2},
    ....
    and the desired output value is tag1.val1

    @param: df - original dataframe
    @param: col_name: name of the coloumn to normalize
    """

    def normalize_coloums(df, col_name, tag):
        tmp_col = df[col_name].copy()
        tmp_col = tmp_col.apply(lambda x: {} if pd.isna(x) else x)
        tmp = pd.json_normalize(tmp_col.copy())

        if tag not in tmp.columns:
            return pd.Series(name=col_name)

        col1 = tmp[tag].to_numpy()
        col1_series = pd.Series(col1, name=col_name)
        return col1_series

    def create_df(df, sub_cat, cols, normalizable_cols):

        if f'cv.{sub_cat}' not in df.columns:
            return pd.DataFrame(columns=cols)

        cat_dict = df['cv.' + sub_cat].copy()

        user_ids = df['user_id'].copy()
        tmp_df = create_from_topic('user_id', user_ids, cat_dict)
        if tmp_df is not None:
            tmp_df = tmp_df[cols].copy()
        else:
            return pd.DataFrame()

        for col in normalizable_cols:
            tmp_df[col] = normalize_coloums(tmp_df, col, 'no')
            tmp_df[col].replace(np.nan, '', regex=True, inplace=True)

        return tmp_df

    """
    Create a semi-colon seperated string list of values from a list of nested dictonaries
     df_col: [
                {
                tag: {
                        sub_tag: "Yarn",
                     },
                },
                {
                tag: {
                        sub_tag: "VS Code"
                     }
                }
            ]
    gives
    "Yarn;VSCode"

    @param df - input dataframe
    @param df_col - specified df coloumn to ectract values from
    @param new_col_name - new name of coloumn for renaming purposes
    @param tag - key on othermost dictonary
    @param sub_tag - key on innermost dictonary
    """

    def make_custom_lists(tmp, df_col, new_col_name, tag, sub_tag):
        out_tmp = tmp.copy()
        new_col = []
        for col_list in df_col:
            if not isinstance(col_list, list):
                new_col.append("")
                continue
            tmp_string = ""
            for elem in col_list:
                f_string = none_to_empty_str(elem.get(tag, {}).get(sub_tag, '')) \
                    if elem is not None and elem.get(tag, {}) is not None else ''
                tmp_string = tmp_string + ";" + f"{f_string}"
            new_col.append(tmp_string[1:])
        out_tmp[new_col_name] = new_col
        return out_tmp

    def create_education_df(df):
        education_df_coloums = ['user_id', 'degree', 'description', 'month_from',
                                'month_to', 'school', 'year_from', 'year_to']
        edu_normalizable_cols = ['degree', 'description', 'school']
        education_df = create_df(
            df, 'educations', education_df_coloums, edu_normalizable_cols)
        education_df['month_to'] = column_type_to_int(education_df['month_to'])
        education_df['year_to'] = column_type_to_int(education_df['year_to'])
        education_df['month_from'] = column_type_to_int(
            education_df['month_from'])
        education_df['year_from'] = column_type_to_int(
            education_df['year_from'])

        return education_df

    def create_blogs_df(df):
        blogs_df_columns = ['user_id', 'long_description',
                            'month', 'name', 'url', 'year']
        normalizable_cols = ['long_description', 'name']
        blogs_df = create_df(df, 'blogs', blogs_df_columns, normalizable_cols)
        blogs_df['month'] = column_type_to_int(blogs_df['month'])
        blogs_df['year'] = column_type_to_int(blogs_df['year'])
        return blogs_df

    def create_courses_df(df):
        courses_df_columns = ['user_id',
                              'long_description', 'name', 'program', 'year']
        normalizable_cols = ['long_description', 'name', 'program']
        courses_df = create_df(
            df, 'courses', courses_df_columns, normalizable_cols)
        return courses_df

    def create_key_qualification_df(df):
        df_columns = ['user_id', 'long_description', 'label', 'tag_line']
        normalizable_cols = ['long_description', 'label', 'tag_line']
        key_qualification_df = create_df(
            df, 'key_qualifications', df_columns, normalizable_cols)
        return key_qualification_df

    def create_languages_df(df):
        df_columns = ['user_id', 'name', 'level']
        normalizable_cols = ['name', 'level']
        languages_df = create_df(
            df, 'languages', df_columns, normalizable_cols)
        return languages_df

    def create_project_experiences_df(df):
        df_columns = ['user_id', 'customer', 'description', 'long_description', 'industry',
                      'project_experience_skills', 'roles', "percent_allocated", 'year_from',
                      'year_to', 'month_from', 'month_to']
        normalizable_cols = ['customer',
                             'long_description', 'description', 'industry']

        project_experiences_df = create_df(
            df, 'project_experiences', df_columns, normalizable_cols)
        project_experiences_df['month_to'] = column_type_to_int(
            project_experiences_df['month_to'])
        project_experiences_df['year_to'] = column_type_to_int(
            project_experiences_df['year_to'])
        project_experiences_df['month_from'] = column_type_to_int(
            project_experiences_df['month_from'])
        project_experiences_df['year_from'] = column_type_to_int(
            project_experiences_df['year_from'])
        project_experiences_df['percent_allocated'] = column_type_to_int(
            project_experiences_df['percent_allocated'])

        project_experiences_df = make_custom_lists(
            project_experiences_df,
            project_experiences_df['project_experience_skills'], 'project_experience_skills', 'tags', 'no')

        project_experiences_df = make_custom_lists(
            project_experiences_df,
            project_experiences_df['roles'], 'roles', 'name', 'no')

        return project_experiences_df

    def create_technologies_df(df):
        df_columns = ['user_id', 'category', 'technology_skills']
        normalizable_cols = ['category']
        technologies_df = create_df(
            df, 'technologies', df_columns, normalizable_cols)
        technologies_df = make_custom_lists(technologies_df,
                                            technologies_df['technology_skills'],
                                            'technology_skills', 'tags', 'no')
        return technologies_df

    def create_work_experiences_df(df):
        df_columns = ['user_id', 'description', 'employer', 'month_from', 'month_to', 'year_from',
                      'year_to', 'long_description']
        work_normalizable_cols = [
            'description', 'employer', 'long_description']
        work_experiences_df = create_df(
            df, 'work_experiences', df_columns, work_normalizable_cols)
        work_experiences_df['month_to'] = column_type_to_int(
            work_experiences_df['month_to'])
        work_experiences_df['month_from'] = column_type_to_int(
            work_experiences_df['month_from'])
        work_experiences_df['year_to'] = column_type_to_int(
            work_experiences_df['year_to'])
        work_experiences_df['year_from'] = column_type_to_int(
            work_experiences_df['year_from'])

        return work_experiences_df

    return {
        'cv_partner_employees': employee_df,
        'cv_partner_education': create_education_df(df),
        'cv_partner_blogs': create_blogs_df(df),
        'cv_partner_courses': create_courses_df(df),
        'cv_partner_key_qualification': create_key_qualification_df(df),
        'cv_partner_languages': create_languages_df(df),
        'cv_partner_project_experience': create_project_experiences_df(df),
        'cv_partner_technology_skills': create_technologies_df(df),
        'cv_partner_work_experience': create_work_experiences_df(df)
    }

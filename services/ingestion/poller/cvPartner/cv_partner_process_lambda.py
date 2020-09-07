from dataplattform.common.handlers.process import ProcessHandler
from typing import Dict
import pandas as pd
import numpy as np


handler = ProcessHandler()


@handler.process(partitions={})
def process(data, events) -> Dict[str, pd.DataFrame]:
    def make_dataframe(d):
        d = d.json()
        payload = d['data']
        df = pd.json_normalize(payload)
        return df

    employee_table = [
        'user_id',
        'default_cv_id',
        'image',
        'cv_link',
        'cv.navn',
        'cv.email',
        'cv.telefon',
        'cv.born_year',
        'cv.nationality.int',
        'cv.place_of_residence.int',
        'cv.twitter',
        'cv.title.no'
        ]

    df = pd.concat([make_dataframe(d) for d in data])
    employee_df = df[employee_table].copy()
    employee_df.fillna(pd.NA, inplace=True)
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
            return pd.DataFrame.from_records(np.array([{elem_tag: list1_elem, **x} for x in topic]))
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
        col1 = tmp[tag].to_numpy()
        col1_series = pd.Series(col1, name=col_name)
        col1_series_out = col1_series.replace(np.nan, '', regex=True)
        return col1_series_out

    def create_df(df, sub_cat, cols, normalizable_cols):
        cat_dict = df['cv.' + sub_cat].copy()
        user_ids = df['user_id'].copy()
        tmp_df = create_from_topic('user_id', user_ids, cat_dict)[cols].copy()
        for col in normalizable_cols:
            tmp_df[col] = normalize_coloums(tmp_df, col, 'no')

        tmp_df.fillna(pd.NA, inplace=True)
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
                tmp_string = tmp_string + ";" + elem.get(tag, {}).get(sub_tag, '')
            new_col.append(tmp_string[1:])
        out_tmp[new_col_name] = new_col
        return out_tmp

    def create_month_year_string(month, year):
        return month + "/" + year

    def create_education_df(df):
        education_df_coloums = ['user_id', 'degree', 'description', 'month_from',
                                'month_to', 'school', 'year_from', 'year_to']
        edu_normalizable_cols = ['degree', 'description', 'school']
        tmp = create_df(df, 'educations', education_df_coloums, edu_normalizable_cols)
        tmp['time_from'] = create_month_year_string(tmp['month_from'], tmp['year_from'])
        tmp['time_to'] = create_month_year_string(tmp['month_to'], tmp['year_to'])

        return tmp

    def create_blogs_df(df):
        blogs_df_columns = ['user_id', 'long_description', 'month', 'name', 'url', 'year']
        normalizable_cols = ['long_description', 'name']
        tmp = create_df(df, 'blogs', blogs_df_columns, normalizable_cols)
        tmp['time'] = create_month_year_string(tmp['month'], tmp['year'])
        return tmp

    def create_courses_df(df):
        courses_df_columns = ['user_id', 'long_description', 'name', 'program', 'year']
        normalizable_cols = ['long_description', 'name', 'program']
        tmp = create_df(df, 'courses', courses_df_columns, normalizable_cols)
        return tmp

    def create_key_qualification_df(df):
        df_columns = ['user_id', 'long_description', 'label', 'tag_line']
        normalizable_cols = ['long_description', 'label', 'tag_line']
        tmp = create_df(df, 'key_qualifications', df_columns, normalizable_cols)
        return tmp

    def create_languages_df(df):
        df_columns = ['user_id', 'name', 'level']
        normalizable_cols = ['name', 'level']
        tmp = create_df(df, 'languages', df_columns, normalizable_cols)
        return tmp

    def create_project_experiences_df(df):
        df_columns = ['user_id', 'customer', 'description', 'long_description', 'industry',
                      'project_experience_skills', 'roles', "percent_allocated", 'year_from',
                      'year_to', 'month_from', 'month_to']
        normalizable_cols = ['customer', 'long_description', 'description', 'industry']

        tmp = create_df(df, 'project_experiences', df_columns, normalizable_cols)

        tmp = make_custom_lists(tmp, tmp['project_experience_skills'], 'project_experience_skills', 'tags', 'no')
        tmp = make_custom_lists(tmp, tmp['roles'], 'roles', 'name', 'no')
        tmp['time_from'] = create_month_year_string(tmp['month_from'], tmp['year_from'])
        tmp['time_to'] = create_month_year_string(tmp['month_to'], tmp['year_to'])

        return tmp

    def create_technologies_df(df):
        df_columns = ['user_id', 'category', 'technology_skills']
        normalizable_cols = ['category']
        tmp = create_df(df, 'technologies', df_columns, normalizable_cols)
        tmp = make_custom_lists(tmp, tmp['technology_skills'], 'technology_skills', 'tags', 'no')
        return tmp

    def create_work_experiences_df(df):
        df_columns = ['user_id', 'description', 'employer', 'month_from', 'month_to', 'year_from',
                      'year_to', 'long_description']
        work_normalizable_cols = ['description', 'employer', 'long_description']
        tmp = create_df(df, 'work_experiences', df_columns, work_normalizable_cols)
        tmp['time_from'] = create_month_year_string(tmp['month_from'], tmp['year_from'])
        tmp['time_to'] = create_month_year_string(tmp['month_to'], tmp['year_to'])
        return tmp

    return {
        'employee_data': employee_df,
        'education_data': create_education_df(df),
        'blogs_data': create_blogs_df(df),
        'courses_data': create_courses_df(df),
        'key_qualification_data': create_key_qualification_df(df),
        'languages_data': create_languages_df(df),
        'project_experience_data': create_project_experiences_df(df),
        'technology_skills_data': create_technologies_df(df),
        'work_experience_data': create_work_experiences_df(df)
    }

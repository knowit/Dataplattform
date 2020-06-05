testLists = [['', 'a', 'b', ''], ['', 1, 2, ''], ['', 2, 3, ''], ['', '', '', '']]
new_list = []


def is_all_zero(row_list):
    for i in range(0, len(row_list)):
        if row_list[i] != '' and row_list[0] is not None:
            return False
    return True


def is_valid_field(field):
    if (field != '' and field is not None):
        return True
    return False


def find_valid_coloums(coloum_row):
    first_indx = 0
    last_indx = len(coloum_row) - 1
    for i in range(0, len(coloum_row)):
        if is_valid_field(coloum_row[i]):
            first_indx = i
            break

    for i in range(0, len(coloum_row)):
        j = len(coloum_row) - i - 1
        if is_valid_field(coloum_row[j]):
            last_indx = j
            break

    return first_indx, last_indx


for i in range(0, len(testLists)):
    if not is_all_zero(testLists[i]):
        new_list.append(testLists[i])

a, b = find_valid_coloums(new_list[0])
print(a, b)
new_list2 = []
for i in range(0, len(new_list)):
    stripped_list = new_list[i][a:b+1]
    new_list2.append(stripped_list)

print(new_list2)



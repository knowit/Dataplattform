

class Temp_repository:
    test_data = [
        {"name": "Testersen", "age": 73},
        {"name": "Bjarne", "age": 7},
        {"name": "Potet", "age": 22}
    ]

    def get_all(self):
        return self.test_data

    def get_person_by_name(self, name):
        return [x for x in self.test_data if x['name'] == name]

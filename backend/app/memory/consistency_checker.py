class ConsistencyChecker:
    def __init__(self):
        pass

    def demographic_validation(self, persona):
        required = ["name", "age", "gender", "occupation"]

        for field in required:
            if field not in persona:
                return False

        return True

    def behavior_validation(self, opinions):
        if len(opinions) == 0:
            return False

        return True

    def consistency_score(self, total, consistent):
        if total == 0:
            return 0

        return round((consistent / total) * 100, 2)
        
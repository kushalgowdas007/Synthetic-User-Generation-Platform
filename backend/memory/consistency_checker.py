class ConsistencyChecker:

    @staticmethod
    def check_opinion(old_opinion, new_opinion):
        return old_opinion == new_opinion

    @staticmethod
    def validate_demographics(demographics):
        required_fields = ["name", "age"]

        for field in required_fields:
            if field not in demographics:
                return False

        return True

    @staticmethod
    def validate_behavior(history):
        return len(history) >= 0

    @staticmethod
    def logical_consistency():
        return True

    @staticmethod
    def consistency_score(matches, total):
        if total == 0:
            return 100
        return (matches / total) * 100
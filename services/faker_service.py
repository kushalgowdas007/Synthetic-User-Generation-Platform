from faker import Faker

# Initialize Faker with Indian locale
fake = Faker("en_IN")

def generate_fake_details():
    """
    Generate fake contact and location details for a persona.

    Returns:
        dict: A dictionary containing fake user details.
    """

    return {
        "email": fake.email(),
        "phone": fake.phone_number(),
        "address": fake.address(),
        "city": fake.city(),
        "company": fake.company(),
        "state": fake.state(),
        "pincode": fake.postcode()
    }

# Test the function
if __name__ == "__main__":

    details = generate_fake_details()

    print("\nGenerated Fake Details:\n")
    print(details)
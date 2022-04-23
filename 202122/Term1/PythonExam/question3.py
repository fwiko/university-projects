def int_input(message: str) -> int:
    while True:
        try:
            user_input = int(input(message))
        except ValueError:
            print("Invalid input. Please try again.")
        else:
            return user_input


def main():
    repeat = "y"

    while repeat == "y":
        test_a = int_input("Enter the result for test A: ")
        test_b = int_input("Enter the result for test B: ")
        test_c = int_input("Enter the result for test C: ")

        final_iq = (test_a + test_b) / test_c

        if final_iq > 180:
            skill_level = "Genius"
        elif final_iq > 120:
            skill_level = "Highly Intelligent"
        else:
            skill_level = "Normal"

        print("Final IQ:", final_iq)
        print(f"This IQ indicates a {skill_level} skill level")

        while True:
            repeat = input("Would you like to calculate another test? (y/n): ").lower()
            if repeat in ("y", "n"):
                break
            else:
                print("Invalid input. Please input either 'y' or 'n'.")


if __name__ == "__main__":
    main()

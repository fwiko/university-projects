
def int_input(message: str) -> int:
    """requires user to input a numeric/integer value to be successful"""
    while True:
        try:
            user_input = int(input(message))
        except ValueError:
            print("Invalid input. Please try again.")
        else:
            return user_input

def main():
    """main program function - IQ calculator based on test results"""
    repeat = 'y'
    iq_list = []
    
    while repeat == 'y':
        test_a = int_input("Enter the result for test A: ")
        test_b = int_input("Enter the result for test B: ")
        test_c = int_input("Enter the result for test C: ")
        
        final_iq = (test_a+test_b)/test_c
        
        iq_list.append(final_iq)
        
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
            if repeat in ('y', 'n'):
                break
            else:
                print("Invalid input. Please input either 'y' or 'n'.")
    
    print(f"A total of {len(iq_list)} IQs were calculated, with a average value of {sum(iq_list)/len(iq_list)}.")


if __name__ == "__main__":
    main()

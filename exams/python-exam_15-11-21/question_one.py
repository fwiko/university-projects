def main():
    test_a = 500
    test_b = 700
    test_c = 15
    
    final_iq = (test_a+test_b)/test_c
    
    if final_iq > 180:
        skill_level = "Genius"
    elif final_iq > 120:
        skill_level = "Highly Intelligent"
    else:
        skill_level = "Normal"
    
    print("Final IQ:", final_iq)
    print(f"This IQ indicates a {skill_level} skill level")
    

if __name__ == "__main__":
    main()

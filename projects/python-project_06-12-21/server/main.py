import modules

def main() -> None:
    """main function for the server"""
    server = modules.Server("0.0.0.0", 5050)
    print(server)
    
if __name__ == "__main__":
    main()
    
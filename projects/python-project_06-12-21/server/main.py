from quizgame import Server

def main() -> None:
    """main function for the server"""
    server = Server("0.0.0.0", 5050)
    server.start()
    
if __name__ == "__main__":
    main()
    
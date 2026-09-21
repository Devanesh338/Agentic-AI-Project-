import sys
import traceback
import runpy

def main():
    try:
        # Redirect stderr to a log file
        log_file = open("C:\\Users\\daksh\\OneDrive\\Documents\\My Projects\\Multi_Agent_System_With_Mcp2\\mcp_wrapper_error.log", "w")
        sys.stderr = log_file
        
        # Run the actual server
        runpy.run_path("C:\\Users\\daksh\\OneDrive\\Documents\\My Projects\\Multi_Agent_System_With_Mcp2\\booking_system\\mcp_server\\booking_mcp_server.py", run_name="__main__")
    except Exception as e:
        traceback.print_exc(file=log_file)
    finally:
        log_file.close()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Wrapper script to run pelabuhan folder scripts from the root directory
"""

import os
import sys
import subprocess

def run_pelabuhan_script(script_name):
    """Run a script from the pelabuhan folder"""
    
    script_path = os.path.join('pelabuhan', script_name)
    
    if not os.path.exists(script_path):
        print(f"Script not found: {script_path}")
        return False
    
    print(f"Running {script_name} from pelabuhan folder...")
    
    try:
        # Change to pelabuhan directory and run the script
        original_dir = os.getcwd()
        os.chdir('pelabuhan')
        
        # Run the script
        result = subprocess.run([sys.executable, script_name], capture_output=True, text=True)
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Warnings/Errors: {result.stderr}")
        
        # Return to original directory
        os.chdir(original_dir)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running {script_name}: {e}")
        # Try to return to original directory
        try:
            os.chdir(original_dir)
        except:
            pass
        return False

def main():
    """Main function to provide menu for running pelabuhan scripts"""
    
    print("Pelabuhan Script Runner")
    print("=" * 40)
    print("Available scripts:")
    print("1. pelabuhan_weather.py - Collect weather data from all ports")
    print("2. extract_failed_data.py - Extract failed data fetches")
    print("3. create_port_data.py - Create simplified port data")
    print("4. Run all scripts in sequence")
    
    try:
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            success = run_pelabuhan_script('pelabuhan_weather.py')
        elif choice == '2':
            success = run_pelabuhan_script('extract_failed_data.py')
        elif choice == '3':
            success = run_pelabuhan_script('create_port_data.py')
        elif choice == '4':
            print("\nRunning all scripts in sequence...")
            scripts = ['pelabuhan_weather.py', 'extract_failed_data.py', 'create_port_data.py']
            all_success = True
            
            for script in scripts:
                print(f"\n--- Running {script} ---")
                if not run_pelabuhan_script(script):
                    all_success = False
                    print(f"{script} failed")
                else:
                    print(f"{script} completed successfully")
            
            success = all_success
        else:
            print("Invalid choice. Please select 1-4.")
            return
        
        if success:
            print(f"\nOperation completed successfully!")
        else:
            print(f"\nOperation failed!")
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main() 
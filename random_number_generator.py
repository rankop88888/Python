import random
import time
import os

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_numbers(numbers, rolling_positions=None, final_positions=None):
    """Print numbers with visual styling"""
    print("\n" + "="*50)
    print("🎰 ROLLING NUMBER GENERATOR 🎰")
    print("="*50)
    print()
    
    # Print numbers with styling
    display_line = ""
    status_line = ""
    
    for i, num in enumerate(numbers):
        if rolling_positions and i in rolling_positions:
            display_line += f"[{num}] "
            status_line += " ⚡  "
        elif final_positions and i in final_positions:
            display_line += f" {num}  "
            status_line += " ✅  "
        else:
            display_line += f" {num}  "
            status_line += "    "
    
    print(f"    {display_line}")
    print(f"    {status_line}")
    print()

def roll_numbers_slowly():
    """Main rolling function with slow, visible animation"""
    
    print("🎲 Starting slow number rolling...")
    print("Settings:")
    
    # Get user preferences
    try:
        roll_speed = float(input("Rolling speed (seconds between changes, default 0.3): ") or "0.3")
        total_duration = float(input("Total duration (seconds, default 4.0): ") or "4.0")
        num_digits = int(input("Number of digits (default 8): ") or "8")
    except ValueError:
        print("Using default settings...")
        roll_speed = 0.3
        total_duration = 4.0
        num_digits = 8
    
    print(f"\nRolling {num_digits} digits for {total_duration} seconds at {roll_speed}s intervals...")
    input("Press Enter to start rolling...")
    
    # Generate final target numbers
    final_numbers = [random.randint(0, 9) for _ in range(num_digits)]
    
    # Initialize current numbers
    current_numbers = [0] * num_digits
    
    # Calculate steps and timing
    total_steps = int(total_duration / roll_speed)
    
    print(f"\n🎯 Target numbers: {final_numbers}")
    print("=" * 50)
    
    # Rolling animation
    for step in range(total_steps + 1):
        clear_screen()
        
        # Calculate progress
        progress = step / total_steps if total_steps > 0 else 1
        
        # Determine which positions are still rolling
        rolling_positions = set()
        final_positions = set()
        
        for i in range(num_digits):
            # Each position stops at a different time (cascade effect)
            position_stop_point = 0.3 + (i * 0.7 / num_digits)  # Stop between 30% and 100% progress
            
            if progress >= position_stop_point:
                # This position has stopped
                current_numbers[i] = final_numbers[i]
                final_positions.add(i)
            else:
                # Still rolling
                current_numbers[i] = random.randint(0, 9)
                rolling_positions.add(i)
        
        # Display current state
        print_numbers(current_numbers, rolling_positions, final_positions)
        
        # Progress bar
        progress_width = 40
        filled_width = int(progress * progress_width)
        progress_bar = "█" * filled_width + "░" * (progress_width - filled_width)
        print(f"Progress: [{progress_bar}] {progress*100:.1f}%")
        
        # Status
        if progress < 1:
            rolling_count = len(rolling_positions)
            print(f"Status: {rolling_count} digits still rolling...")
        else:
            print("Status: ✅ All digits stopped!")
        
        # Wait before next update
        if step < total_steps:
            time.sleep(roll_speed)
    
    # Final display with statistics
    print("\n" + "="*50)
    print("🎉 FINAL RESULTS 🎉")
    print("="*50)
    print_numbers(final_numbers, final_positions=set(range(num_digits)))
    
    # Statistics
    total = sum(final_numbers)
    average = total / len(final_numbers)
    print(f"📊 Statistics:")
    print(f"   Sum: {total}")
    print(f"   Average: {average:.1f}")
    print(f"   Max: {max(final_numbers)}")
    print(f"   Min: {min(final_numbers)}")
    print(f"   Range: {max(final_numbers) - min(final_numbers)}")
    
    return final_numbers

def main():
    """Main program loop"""
    print("Welcome to the Slow Rolling Number Generator!")
    
    while True:
        try:
            roll_numbers_slowly()
            
            print("\n" + "="*50)
            again = input("\nRoll again? (y/n): ").lower().strip()
            if again not in ['y', 'yes']:
                break
                
        except KeyboardInterrupt:
            print("\n\nThanks for using the Rolling Number Generator!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            continue
    
    print("Goodbye! 🎰")

if __name__ == "__main__":
    main()


# Grade System

mark = float(input("Enter your mark (0-100): "))

if mark < 0 or mark > 100:
    print(f"Entered mark: {mark}")
    print("Grade: Invalid mark")
elif mark >= 90:
    print(f"Entered mark: {mark}")
    print("Grade: A")
elif mark >= 80:
    print(f"Entered mark: {mark}")
    print("Grade: B")
elif mark >= 70:
    print(f"Entered mark: {mark}")
    print("Grade: C")
elif mark >= 60:
    print(f"Entered mark: {mark}")
    print("Grade: D")
else:
    print(f"Entered mark: {mark}")
    print("Grade: F")

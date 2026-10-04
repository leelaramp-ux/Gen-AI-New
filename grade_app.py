
import streamlit as st


# -----------------------------
# Grade function from Day 2
# -----------------------------
def get_grade(mark):
    if mark >= 90:
        return "A"
    elif mark >= 80:
        return "B"
    elif mark >= 70:
        return "C"
    elif mark >= 60:
        return "D"
    elif mark >= 50:
        return "E"
    else:
        return "F"


# -----------------------------
# Keep students between reruns
# -----------------------------
if "students" not in st.session_state:
    st.session_state.students = []


# -----------------------------
# Page title
# -----------------------------
st.title("Student Grade Manager")

st.write("Add students and their marks below.")


# -----------------------------
# Add Student Form
# -----------------------------
with st.form("add"):

    name = st.text_input("Name")

    mark = st.number_input(
        "Mark",
        min_value=0,
        max_value=100,
        value=0
    )

    if st.form_submit_button("Add"):

        if name.strip() == "":
            st.error("Please enter a student name.")

        else:
            student = {
                "Name": name.strip(),
                "Mark": mark,
                "Grade": get_grade(mark)
            }

            st.session_state.students.append(student)

            st.success("Student added successfully!")


# -----------------------------
# Show Students
# -----------------------------
if st.session_state.students:

    st.subheader("Student Results")

    st.table(st.session_state.students)

    # Get marks for calculations
    marks = [
        student["Mark"]
        for student in st.session_state.students
    ]

    # Class calculations
    average = sum(marks) / len(marks)
    highest = max(marks)
    lowest = min(marks)

    # Show metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Class Average", f"{average:.2f}")

    with col2:
        st.metric("Highest", highest)

    with col3:
        st.metric("Lowest", lowest)

else:

    st.info("No students added yet.")



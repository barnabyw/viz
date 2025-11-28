from data_prep import load_caiso_folder
from animation import animate_trailing_yearly_stack

if __name__ == "__main__":
    data_path = r"C:\Users\barna\OneDrive\Documents\data\caiso\raw_years"
    df = load_caiso_folder(data_path)

    animate_trailing_yearly_stack(df, fps=60)

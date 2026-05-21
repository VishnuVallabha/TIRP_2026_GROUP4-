
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

from config import RESULT_COLORS
from model_loader import load_or_train, force_retrain

# ── Load / train on startup ───────────────────────────────────────
(preprocessor, label_encoder, best_model,
 top3_models, results_df, best_model_name) = load_or_train()


def get_result_color(result):
    return RESULT_COLORS.get(result.lower(), "white")


def analyse_input():
    global preprocessor, label_encoder, best_model, top3_models, results_df, best_model_name
    try:
        sym_text = symptom_text_var.get("1.0", tk.END).strip()
        if not sym_text:
            messagebox.showerror("Error", "Please describe your symptoms.")
            return

        # ── Map SACA questions → CSV columns ─────────────────────
        # Q2 pain level (1-10) → estimate heart_rate
        pain_val    = int(pain_var.get())
        heart_rate  = 70 + (pain_val * 5)          # mild pain=75, severe=120

        # Q3 fever → temperature value
        fever_map   = {"No fever": 36.8, "Low (37-38)": 37.5,
                       "High (38-39)": 38.5, "Very high (39+)": 39.5}
        temperature = fever_map.get(fever_var.get(), 36.8)

        # Q4 breathing difficulty + Q6 activity → breathing_rate
        breathe_boost = {"Normal": 0, "Slightly difficult": 3,
                         "Very difficult": 7, "Cannot breathe": 12}
        activity_boost = {"4 - Normal": 0, "3 - Mostly OK": 1,
                          "2 - Struggling": 2, "1 - Cannot function": 4}
        breathing_rate = (16
                          + breathe_boost.get(breathe_var.get(), 0)
                          + activity_boost.get(activity_var.get(), 0))

        age_val = int(age_var.get())

        input_data = {
            "symptom_text":  sym_text,
            "age":           age_val,
            "heart_rate":    heart_rate,
            "temperature":   temperature,
            "breathing_rate": breathing_rate,
        }

        proc_input = preprocessor.transform(pd.DataFrame([input_data]))

        # ── Display results ───────────────────────────────────────
        result_box.config(state="normal")
        result_box.delete("1.0", tk.END)

        # Section 1 — Top 3 metrics table
        W = 108
        result_box.insert(tk.END, "TOP 3 BEST ALGORITHM COMBINATIONS — TEST METRICS\n")
        result_box.insert(tk.END, "=" * W + "\n")
        result_box.insert(tk.END,
            f"{'Rank':<7}{'Model':<22}{'Accuracy':<12}{'Precision':<12}"
            f"{'Recall':<12}{'F1-Score':<12}{'Severe Recall':<13}\n")
        result_box.insert(tk.END, "-" * W + "\n")

        for rank, (_, row) in enumerate(results_df.iterrows(), start=1):
            tag = "★ BEST" if rank == 1 else f"  #{rank}   "
            result_box.insert(tk.END,
                f"{tag:<7}{row['Model']:<22}"
                f"{row['Accuracy']:<12}"
                f"{row['Precision_Weighted']:<12}"
                f"{row['Recall_Weighted']:<12}"
                f"{row['F1_Weighted']:<12}"
                f"{row['Severe_Recall']:<13}\n")

        result_box.insert(tk.END,
            "\nRanking: Severe Recall → F1-Score → Accuracy\n")

        # Section 2 — Per-model prediction for this patient
        result_box.insert(tk.END, "\nCURRENT PATIENT — PREDICTIONS FROM TOP 3\n")
        result_box.insert(tk.END, "=" * W + "\n")
        result_box.insert(tk.END,
            f"{'Model':<22}{'Prediction':<15}{'Final Decision?':<15}\n")
        result_box.insert(tk.END, "-" * W + "\n")

        for name, model in top3_models.items():
            pred  = model.predict(proc_input)
            label = label_encoder.inverse_transform(pred)[0]
            flag  = "✓ YES" if name == best_model_name else "  NO"
            result_box.insert(tk.END, f"{name:<22}{label:<15}{flag:<15}\n")

        # Section 3 — Final result
        final_label = label_encoder.inverse_transform(
            best_model.predict(proc_input))[0]
        best_row = results_df.iloc[0]

        result_box.insert(tk.END, "\nFINAL RECOMMENDED OUTPUT\n")
        result_box.insert(tk.END, "=" * W + "\n")
        result_box.insert(tk.END, f"Triage Result  :  {final_label.upper()}\n")
        result_box.insert(tk.END, f"Best Algorithm :  {best_model_name}\n")
        result_box.insert(tk.END, f"Accuracy       :  {best_row['Accuracy']}\n")
        result_box.insert(tk.END, f"Precision      :  {best_row['Precision_Weighted']}\n")
        result_box.insert(tk.END, f"Recall         :  {best_row['Recall_Weighted']}\n")
        result_box.insert(tk.END, f"F1-Score       :  {best_row['F1_Weighted']}\n")
        result_box.insert(tk.END, f"Severe Recall  :  {best_row['Severe_Recall']}\n")
        result_box.insert(tk.END,
            "\n7 combinations evaluated (3 individual + 3 two-way + 1 three-way).\n"
            "Only the best 3 are shown above.\n")

        result_box.config(state="disabled")

        final_result_label.config(
            text=f"  Final Result: {final_label.upper()}   |   Best Algorithm: {best_model_name}  ",
            bg=get_result_color(final_label)
        )

    except ValueError:
        messagebox.showerror("Input Error", "Please check Age and Pain fields — must be numbers.")
    except Exception as e:
        messagebox.showerror("Error", str(e))


def retrain():
    global preprocessor, label_encoder, best_model, top3_models, results_df, best_model_name
    (preprocessor, label_encoder, best_model,
     top3_models, results_df, best_model_name) = force_retrain()
    subtitle.config(text=f"7 combinations evaluated → best 3 shown  |  Current best: {best_model_name}")
    messagebox.showinfo("Done", f"Retrained!\nBest: {best_model_name}")


# =========================================================
# GUI
# =========================================================
root = tk.Tk()
root.title("SACA — ML Triage Desktop")
root.geometry("1060x860")
root.configure(bg="#f4f6f8")

tk.Label(root, text="SACA — Adaptive Clinical Assistant",
         font=("Arial", 20, "bold"), bg="#f4f6f8", fg="#1f2d3d").pack(pady=(12, 2))

subtitle = tk.Label(root,
    text=f"7 combinations evaluated → best 3 shown  |  Current best: {best_model_name}",
    font=("Arial", 9), bg="#f4f6f8", fg="#666")
subtitle.pack(pady=(0, 8))

# ── Form ──────────────────────────────────────────────────────────
form = tk.Frame(root, bg="#f4f6f8")
form.pack(pady=4)

def row(r, label, widget_fn, col=0):
    tk.Label(form, text=label, font=("Arial", 11, "bold"),
             bg="#f4f6f8").grid(row=r, column=col, sticky="w", padx=12, pady=6)
    w = widget_fn()
    w.grid(row=r, column=col+1, sticky="w", padx=10)
    return w

# Symptom text — spans full width
tk.Label(form, text="Describe Symptoms", font=("Arial", 11, "bold"),
         bg="#f4f6f8").grid(row=0, column=0, sticky="nw", padx=12, pady=6)
symptom_text_var = tk.Text(form, width=60, height=3, font=("Arial", 10))
symptom_text_var.grid(row=0, column=1, columnspan=3, padx=10, pady=6, sticky="w")

# Q2 pain + Age
pain_var = tk.StringVar(value="5")
age_var  = tk.StringVar(value="30")
tk.Label(form, text="Q2 · Pain level (1–10)", font=("Arial", 11, "bold"),
         bg="#f4f6f8").grid(row=1, column=0, sticky="w", padx=12, pady=6)
tk.Entry(form, textvariable=pain_var, width=8,
         font=("Arial", 10)).grid(row=1, column=1, sticky="w", padx=10)
tk.Label(form, text="Age", font=("Arial", 11, "bold"),
         bg="#f4f6f8").grid(row=1, column=2, sticky="w", padx=12, pady=6)
tk.Entry(form, textvariable=age_var, width=8,
         font=("Arial", 10)).grid(row=1, column=3, sticky="w", padx=10)

# Q3 fever
fever_var = tk.StringVar(value="No fever")
tk.Label(form, text="Q3 · Fever?", font=("Arial", 11, "bold"),
         bg="#f4f6f8").grid(row=2, column=0, sticky="w", padx=12, pady=6)
ttk.Combobox(form, textvariable=fever_var,
             values=["No fever", "Low (37-38)", "High (38-39)", "Very high (39+)"],
             width=18, state="readonly").grid(row=2, column=1, sticky="w", padx=10)

# Q4 breathing
breathe_var = tk.StringVar(value="Normal")
tk.Label(form, text="Q4 · Breathing?", font=("Arial", 11, "bold"),
         bg="#f4f6f8").grid(row=2, column=2, sticky="w", padx=12, pady=6)
ttk.Combobox(form, textvariable=breathe_var,
             values=["Normal", "Slightly difficult", "Very difficult", "Cannot breathe"],
             width=20, state="readonly").grid(row=2, column=3, sticky="w", padx=10)

# Q6 activity
activity_var = tk.StringVar(value="3 - Mostly OK")
tk.Label(form, text="Q6 · Daily activity", font=("Arial", 11, "bold"),
         bg="#f4f6f8").grid(row=3, column=0, sticky="w", padx=12, pady=6)
ttk.Combobox(form, textvariable=activity_var,
             values=["4 - Normal", "3 - Mostly OK", "2 - Struggling", "1 - Cannot function"],
             width=20, state="readonly").grid(row=3, column=1, sticky="w", padx=10)

# ── Buttons ───────────────────────────────────────────────────────
btn_frame = tk.Frame(root, bg="#f4f6f8")
btn_frame.pack(pady=12)

tk.Button(btn_frame, text="  Analyse  ", command=analyse_input,
          font=("Arial", 12, "bold"), bg="#007acc", fg="white",
          width=16).pack(side="left", padx=12)

tk.Button(btn_frame, text="  Retrain Models  ", command=retrain,
          font=("Arial", 11), bg="#6c757d", fg="white",
          width=18).pack(side="left", padx=12)

# ── Result banner ─────────────────────────────────────────────────
final_result_label = tk.Label(root, text="  Final Result: not analysed yet  ",
    font=("Arial", 13, "bold"), bg="white", fg="#1f2d3d",
    width=90, height=2, relief="solid")
final_result_label.pack(pady=6)

# ── Output box ────────────────────────────────────────────────────
result_box = tk.Text(root, width=120, height=20,
                     font=("Consolas", 10), state="disabled")
result_box.pack(padx=16, pady=8)

root.mainloop()

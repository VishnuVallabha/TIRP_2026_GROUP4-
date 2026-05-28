package com.example.saca;

import android.content.Intent;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.widget.Button;
import android.widget.NumberPicker;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

public class PatientInfoActivity extends AppCompatActivity {

    String language = "english";
    String selectedGender = "";
    int selectedAge = 30;

    Button genderMale, genderFemale, genderOther;
    Button nextButton;
    TextView backButton, ageDisplay;
    NumberPicker agePicker;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_patient_info);

        language = getIntent().getStringExtra("language");
        if (language == null) language = "english";

        backButton  = findViewById(R.id.backButton);
        ageDisplay  = findViewById(R.id.ageDisplay);
        agePicker   = findViewById(R.id.agePicker);
        genderMale  = findViewById(R.id.genderMale);
        genderFemale= findViewById(R.id.genderFemale);
        genderOther = findViewById(R.id.genderOther);
        nextButton  = findViewById(R.id.nextButton);

        backButton.setText(AppLanguage.back(language));
        backButton.setOnClickListener(v -> finish());

        // Age picker setup
        agePicker.setMinValue(1);
        agePicker.setMaxValue(100);
        agePicker.setValue(30);
        agePicker.setWrapSelectorWheel(false);
        agePicker.setOnValueChangedListener((picker, oldVal, newVal) -> {
            selectedAge = newVal;
            ageDisplay.setText(String.valueOf(newVal));
        });

        // Gender buttons
        genderMale.setOnClickListener(v -> selectGender("Male", genderMale));
        genderFemale.setOnClickListener(v -> selectGender("Female", genderFemale));
        genderOther.setOnClickListener(v -> selectGender("Other", genderOther));

        nextButton.setText(AppLanguage.next(language));
        nextButton.setOnClickListener(v -> {
            if (selectedGender.isEmpty()) selectedGender = "Other";

            Intent intent = new Intent(PatientInfoActivity.this, MethodActivity.class);
            intent.putExtra("language", language);
            intent.putExtra("age", selectedAge);
            intent.putExtra("gender", selectedGender);
            startActivity(intent);
        });
    }

    private void selectGender(String gender, Button selected) {
        selectedGender = gender;

        // Reset all to white
        resetGenderButtons();

        // Highlight selected
        GradientDrawable bg = new GradientDrawable();
        bg.setColor(Color.parseColor("#1685D9"));
        bg.setCornerRadius(40f);
        selected.setBackground(bg);
        selected.setTextColor(Color.WHITE);
    }

    private void resetGenderButtons() {
        int borderColor = Color.parseColor("#B9C7DA");
        for (Button btn : new Button[]{genderMale, genderFemale, genderOther}) {
            GradientDrawable bg = new GradientDrawable();
            bg.setColor(Color.WHITE);
            bg.setStroke(2, borderColor);
            bg.setCornerRadius(40f);
            btn.setBackground(bg);
            btn.setTextColor(Color.parseColor("#001F3F"));
        }
    }
}
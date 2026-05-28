package com.example.saca;

import android.content.Intent;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.ImageView;

import androidx.appcompat.app.AppCompatActivity;

public class BodyPartActivity extends AppCompatActivity {

    String language = "english";
    int age = 30;
    String gender = "";
    String selectedBodyPart = "";

    TextView backButton;
    Button headBtn, throatBtn, chestBtn, stomachBtn;
    Button armsBtn, legsBtn, backBtn, wholeBodyBtn, startQuestions;

    View headHighlight, throatHighlight, chestHighlight, stomachHighlight;
    View armsHighlight, legsHighlight, wholeHighlight;
    ImageView humanBodyImage;

    // Colour for selected button state
    static final int COLOR_SELECTED = 0xFF1685D9;
    static final int COLOR_DEFAULT_BG = 0xFFFFFFFF;
    static final int COLOR_DEFAULT_BORDER = 0xFFB9C7DA;
    static final int COLOR_DEFAULT_TEXT = 0xFF001F3F;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_body_part);

        language = getIntent().getStringExtra("language");
        age      = getIntent().getIntExtra("age", 30);
        gender   = getIntent().getStringExtra("gender");
        if (language == null) language = "english";
        if (gender == null)   gender   = "";

        backButton    = findViewById(R.id.backButton);
        humanBodyImage= findViewById(R.id.humanBodyImage);

        headBtn      = findViewById(R.id.headBtn);
        throatBtn    = findViewById(R.id.throatBtn);
        chestBtn     = findViewById(R.id.chestBtn);
        stomachBtn   = findViewById(R.id.stomachBtn);
        armsBtn      = findViewById(R.id.armsBtn);
        legsBtn      = findViewById(R.id.legsBtn);
        backBtn      = findViewById(R.id.backBtn);
        wholeBodyBtn = findViewById(R.id.wholeBodyBtn);
        startQuestions = findViewById(R.id.startQuestions);

        headHighlight    = findViewById(R.id.headHighlight);
        throatHighlight  = findViewById(R.id.throatHighlight);
        chestHighlight   = findViewById(R.id.chestHighlight);
        stomachHighlight = findViewById(R.id.stomachHighlight);
        armsHighlight    = findViewById(R.id.armsHighlight);
        legsHighlight    = findViewById(R.id.legsHighlight);
        wholeHighlight   = findViewById(R.id.wholeHighlight);

        backButton.setText(AppLanguage.back(language));
        backButton.setOnClickListener(v -> finish());

        // Apply Yolŋu Matha labels if needed
        headBtn.setText(AppLanguage.head(language));
        throatBtn.setText(AppLanguage.throat(language));
        chestBtn.setText(AppLanguage.chest(language));
        stomachBtn.setText(AppLanguage.stomach(language));
        armsBtn.setText(AppLanguage.arms(language));
        legsBtn.setText(AppLanguage.legs(language));
        backBtn.setText(AppLanguage.backBody(language));
        wholeBodyBtn.setText(AppLanguage.wholeBody(language));
        startQuestions.setText(AppLanguage.startQuestions(language));

        // Body part button clicks
        headBtn.setOnClickListener(v      -> selectBodyPart("Head",         headBtn));
        throatBtn.setOnClickListener(v    -> selectBodyPart("Throat",       throatBtn));
        chestBtn.setOnClickListener(v     -> selectBodyPart("Chest",        chestBtn));
        stomachBtn.setOnClickListener(v   -> selectBodyPart("Stomach",      stomachBtn));
        armsBtn.setOnClickListener(v      -> selectBodyPart("Arms / Hands", armsBtn));
        legsBtn.setOnClickListener(v      -> selectBodyPart("Legs / Feet",  legsBtn));
        backBtn.setOnClickListener(v      -> selectBodyPart("Back",         backBtn));
        wholeBodyBtn.setOnClickListener(v -> selectBodyPart("Whole Body",   wholeBodyBtn));

        // Tapping the body image — map tap to region
        humanBodyImage.setOnClickListener(v -> {
            // default to Whole Body tap on image
            selectBodyPart("Whole Body", wholeBodyBtn);
        });

        startQuestions.setOnClickListener(v -> {
            if (selectedBodyPart.isEmpty()) {
                Toast.makeText(this,
                        AppLanguage.isYolngu(language)
                                ? "Rumbal nhäma maḻŋ'marama" : "Please select a body part first",
                        Toast.LENGTH_SHORT).show();
                return;
            }
            Intent intent = new Intent(BodyPartActivity.this, SymptomActivity.class);
            intent.putExtra("language",  language);
            intent.putExtra("bodyPart",  selectedBodyPart);
            intent.putExtra("age",       age);
            intent.putExtra("gender",    gender);
            startActivity(intent);
        });
    }

    private void selectBodyPart(String bodyPart, Button selectedButton) {
        selectedBodyPart = bodyPart;
        resetAllButtons();
        hideHighlights();

        // Highlight selected button
        GradientDrawable sel = new GradientDrawable();
        sel.setColor(COLOR_SELECTED);
        sel.setStroke(2, COLOR_SELECTED);
        sel.setCornerRadius(40f);
        selectedButton.setBackground(sel);
        selectedButton.setTextColor(Color.WHITE);

        // Show matching highlight on body image
        switch (bodyPart) {
            case "Head":         headHighlight.setVisibility(View.VISIBLE);    break;
            case "Throat":       throatHighlight.setVisibility(View.VISIBLE);  break;
            case "Chest":        chestHighlight.setVisibility(View.VISIBLE);   break;
            case "Stomach":      stomachHighlight.setVisibility(View.VISIBLE); break;
            case "Arms / Hands": armsHighlight.setVisibility(View.VISIBLE);    break;
            case "Legs / Feet":  legsHighlight.setVisibility(View.VISIBLE);    break;
            case "Back":         stomachHighlight.setVisibility(View.VISIBLE); break;
            case "Whole Body":   wholeHighlight.setVisibility(View.VISIBLE);   break;
        }

        // Enable Start Questions button
        startQuestions.setBackgroundTintList(
                android.content.res.ColorStateList.valueOf(Color.parseColor("#1685D9")));
    }

    private void hideHighlights() {
        headHighlight.setVisibility(View.GONE);
        throatHighlight.setVisibility(View.GONE);
        chestHighlight.setVisibility(View.GONE);
        stomachHighlight.setVisibility(View.GONE);
        armsHighlight.setVisibility(View.GONE);
        legsHighlight.setVisibility(View.GONE);
        wholeHighlight.setVisibility(View.GONE);
    }

    private void resetAllButtons() {
        for (Button btn : new Button[]{headBtn,throatBtn,chestBtn,stomachBtn,
                armsBtn,legsBtn,backBtn,wholeBodyBtn}) {
            GradientDrawable def = new GradientDrawable();
            def.setColor(COLOR_DEFAULT_BG);
            def.setStroke(2, COLOR_DEFAULT_BORDER);
            def.setCornerRadius(40f);
            btn.setBackground(def);
            btn.setTextColor(COLOR_DEFAULT_TEXT);
        }
    }
}
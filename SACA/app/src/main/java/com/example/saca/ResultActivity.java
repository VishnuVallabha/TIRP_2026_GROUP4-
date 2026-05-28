package com.example.saca;

import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Environment;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import java.io.File;
import java.io.FileWriter;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class ResultActivity extends AppCompatActivity {

    String language = "english", severity = "MODERATE";
    String bodyPart = "", symptom = "", gender = "";
    int score = 0, age = 30;
    String ansWhen="", ansSeverity="", ansFever="", ansBreathing="", ansDizzy="", ansActivity="";

    TextView backButton, resultTitle, resultYolngu, resultMessage;
    TextView contactStrip, symptomTimestamp;
    LinearLayout actionCardsContainer, summaryContainer;
    Button saveReportButton, startOverButton;

    // Exact Yolngu result names from desktop constants.py CFG dict
    static final String YO_MILD     = "Märr Mäkitj";      // mild
    static final String YO_MODERATE = "Märr Djuy'yun";     // moderate
    static final String YO_SEVERE   = "Märr Djorra'";      // severe

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_result);

        language     = getIntent().getStringExtra("language");
        severity     = getIntent().getStringExtra("severity");
        bodyPart     = getIntent().getStringExtra("bodyPart");
        symptom      = getIntent().getStringExtra("symptom");
        score        = getIntent().getIntExtra("score", 0);
        age          = getIntent().getIntExtra("age", 30);
        gender       = getIntent().getStringExtra("gender");
        ansWhen      = getIntent().getStringExtra("ansWhen");
        ansSeverity  = getIntent().getStringExtra("ansSeverity");
        ansFever     = getIntent().getStringExtra("ansFever");
        ansBreathing = getIntent().getStringExtra("ansBreathing");
        ansDizzy     = getIntent().getStringExtra("ansDizzy");
        ansActivity  = getIntent().getStringExtra("ansActivity");

        if (language     == null) language = "english";
        if (severity     == null) severity = "MODERATE";
        if (bodyPart     == null) bodyPart = "";
        if (symptom      == null) symptom  = "";
        if (gender       == null) gender   = "";
        if (ansWhen      == null) ansWhen      = "—";
        if (ansSeverity  == null) ansSeverity  = "—";
        if (ansFever     == null) ansFever     = "—";
        if (ansBreathing == null) ansBreathing = "—";
        if (ansDizzy     == null) ansDizzy     = "—";
        if (ansActivity  == null) ansActivity  = "—";

        backButton          = findViewById(R.id.backButton);
        resultTitle         = findViewById(R.id.resultTitle);
        resultYolngu        = findViewById(R.id.resultYolngu);
        resultMessage       = findViewById(R.id.resultMessage);
        contactStrip        = findViewById(R.id.contactStrip);
        symptomTimestamp    = findViewById(R.id.symptomTimestamp);
        actionCardsContainer= findViewById(R.id.actionCardsContainer);
        summaryContainer    = findViewById(R.id.summaryContainer);
        saveReportButton    = findViewById(R.id.saveReportButton);
        startOverButton     = findViewById(R.id.startOverButton);

        boolean yo = AppLanguage.isYolngu(language);

        backButton.setText(AppLanguage.back(language));
        backButton.setOnClickListener(v -> finish());

        // Symptom + timestamp
        String ts = new SimpleDateFormat("dd MMM yyyy  HH:mm", Locale.getDefault()).format(new Date());
        symptomTimestamp.setText((symptom.isEmpty() ? "—" : symptom) + "  ·  " + ts);

        // ── Set result by severity ──────────────────────────────
        if (severity.equals("MILD")) {
            resultTitle.setText(yo ? "😊  " + YO_MILD + " — LOW RISK" : "😊  MILD — LOW RISK");
            resultTitle.setBackgroundColor(Color.parseColor("#2E7D32"));
            resultYolngu.setText(YO_MILD);
            resultYolngu.setTextColor(Color.parseColor("#2E7D32"));
            resultMessage.setText(yo ? AppLanguage.mildAdvice(language)
                    : "Rest at home. Monitor your symptoms.");
            resultMessage.setTextColor(Color.parseColor("#2E7D32"));
            resultMessage.setBackgroundColor(Color.parseColor("#F0FFF8"));
            contactStrip.setText("📞  Yirrkala Clinic: (08) 8987 1000  ·  Mon–Fri 8am–5pm");
            contactStrip.setBackgroundColor(Color.parseColor("#2E7D32"));

        } else if (severity.equals("SEVERE")) {
            resultTitle.setText(yo ? "🚨  " + YO_SEVERE + " — CALL 000 NOW" : "🚨  EMERGENCY — CALL 000 NOW");
            resultTitle.setBackgroundColor(Color.parseColor("#D32F2F"));
            resultYolngu.setText(YO_SEVERE);
            resultYolngu.setTextColor(Color.parseColor("#D32F2F"));
            resultMessage.setText(yo ? AppLanguage.severeAdvice(language)
                    : "Call 000 immediately. Do not wait.");
            resultMessage.setTextColor(Color.parseColor("#D32F2F"));
            resultMessage.setBackgroundColor(Color.parseColor("#FFF0F0"));
            contactStrip.setText("📞  000  (Emergency)   ·   Flying Doctor: 1800 625 800  (Free · 24 hrs)");
            contactStrip.setBackgroundColor(Color.parseColor("#D32F2F"));

        } else { // MODERATE
            resultTitle.setText(yo ? "😟  " + YO_MODERATE + " — SEE A DOCTOR" : "😟  MODERATE — SEE A DOCTOR");
            resultTitle.setBackgroundColor(Color.parseColor("#FF6B35"));
            resultYolngu.setText(YO_MODERATE);
            resultYolngu.setTextColor(Color.parseColor("#FF6B35"));
            resultMessage.setText(yo ? AppLanguage.moderateAdvice(language)
                    : "Visit the Yirrkala clinic within 24 hours.");
            resultMessage.setTextColor(Color.parseColor("#FF6B35"));
            resultMessage.setBackgroundColor(Color.parseColor("#FFF8E8"));
            contactStrip.setText("📞  Yirrkala Clinic: (08) 8987 1000  ·  After hours: Gove Hospital (08) 8987 0211");
            contactStrip.setBackgroundColor(Color.parseColor("#FF6B35"));
        }

        // Build action cards (exact desktop STEPS dict)
        buildActionCards();
        buildSummary();

        saveReportButton.setText(AppLanguage.saveReport(language));
        saveReportButton.setOnClickListener(v -> saveReport());

        startOverButton.setText(AppLanguage.startOver(language));
        startOverButton.setOnClickListener(v -> {
            Intent intent = new Intent(ResultActivity.this, MainActivity.class);
            intent.setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(intent); finish();
        });
    }

    // Exact STEPS from desktop s5_result.py
    private void buildActionCards() {
        actionCardsContainer.removeAllViews();
        String[][] steps;
        String accentHex;

        if (severity.equals("MILD")) {
            accentHex = "#2E7D32";
            steps = new String[][]{
                    {"🛏", "Rest",         "Sleep and avoid heavy activity"},
                    {"💧", "Drink water",  "Stay hydrated all day"},
                    {"💊", "Panadol",      "Take if needed for pain/fever"},
                    {"👁", "Watch",        "Return if it gets worse"},
            };
        } else if (severity.equals("SEVERE")) {
            accentHex = "#D32F2F";
            steps = new String[][]{
                    {"📞", "Call 000",    "Free · Tell them where you are"},
                    {"🏥", "Go NOW",      "Hospital immediately · Don't wait"},
                    {"🧍", "Stay still",  "Sit or lie down · Breathe slowly"},
                    {"👫", "Get help",    "Have someone stay with you"},
            };
        } else {
            accentHex = "#FF6B35";
            steps = new String[][]{
                    {"🏥", "Go to clinic",  "Yirrkala clinic within 24 hrs"},
                    {"👫", "Bring help",    "Take a family member with you"},
                    {"📋", "Tell all",      "Share how long and how bad"},
                    {"💊", "Follow advice", "Take all medicine as told"},
            };
        }

        LinearLayout row = null;
        for (int i = 0; i < steps.length; i++) {
            if (i % 2 == 0) {
                row = new LinearLayout(this);
                row.setOrientation(LinearLayout.HORIZONTAL);
                LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
                lp.setMargins(0, 0, 0, 8);
                row.setLayoutParams(lp);
                actionCardsContainer.addView(row);
            }
            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setBackgroundColor(Color.WHITE);
            card.setPadding(20, 18, 20, 18);
            // Add left-side accent border matching desktop
            card.setPadding(16, 18, 16, 18);
            LinearLayout.LayoutParams cp = new LinearLayout.LayoutParams(
                    0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f);
            cp.setMargins(i % 2 == 0 ? 0 : 6, 0, i % 2 == 0 ? 6 : 0, 0);
            card.setLayoutParams(cp);

            TextView emoji = new TextView(this);
            emoji.setText(steps[i][0]);
            emoji.setTextSize(30f);
            card.addView(emoji);

            TextView title = new TextView(this);
            title.setText(steps[i][1]);
            title.setTextSize(14f);
            title.setTextColor(Color.parseColor(accentHex));
            title.setTypeface(null, android.graphics.Typeface.BOLD);
            card.addView(title);

            TextView desc = new TextView(this);
            desc.setText(steps[i][2]);
            desc.setTextSize(12f);
            desc.setTextColor(Color.parseColor("#607B96"));
            card.addView(desc);

            if (row != null) row.addView(card);
        }
    }

    private void buildSummary() {
        summaryContainer.removeAllViews();
        String[][] rows = {
                {"Symptom",    symptom.isEmpty()  ? "—" : symptom},
                {"Body part",  bodyPart.isEmpty() ? "—" : bodyPart},
                {"Age",        age + " years"},
                {"When",       ansWhen},
                {"Severity",   ansSeverity},
                {"Fever",      ansFever},
                {"Breathing",  ansBreathing},
                {"Sick/Dizzy", ansDizzy},
                {"Activity",   ansActivity},
        };
        for (String[] row : rows) {
            LinearLayout r = new LinearLayout(this);
            r.setOrientation(LinearLayout.HORIZONTAL);
            r.setPadding(0, 5, 0, 5);

            TextView lbl = new TextView(this);
            lbl.setText(row[0] + ": ");
            lbl.setTextSize(13f);
            lbl.setTextColor(Color.parseColor("#6C8DB5"));
            lbl.setLayoutParams(new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));
            r.addView(lbl);

            TextView val = new TextView(this);
            val.setText(row[1]);
            val.setTextSize(13f);
            val.setTextColor(Color.parseColor("#001F3F"));
            val.setTypeface(null, android.graphics.Typeface.BOLD);
            val.setLayoutParams(new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 2f));
            r.addView(val);

            summaryContainer.addView(r);
        }
    }

    private void saveReport() {
        try {
            String ts = new SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(new Date());
            String tsFull = new SimpleDateFormat("dd MMM yyyy  HH:mm:ss", Locale.getDefault()).format(new Date());
            StringBuilder sb = new StringBuilder();
            sb.append("============================================================\n");
            sb.append("  SACA — TRIAGE REPORT\n");
            sb.append("  Generated : ").append(tsFull).append("\n");
            sb.append("============================================================\n\n");
            sb.append("  Symptom      : ").append(symptom).append("\n");
            sb.append("  Body part    : ").append(bodyPart).append("\n");
            sb.append("  Onset        : ").append(ansWhen).append("\n");
            sb.append("  Severity     : ").append(ansSeverity).append("\n");
            sb.append("  Temperature  : ").append(ansFever).append("\n");
            sb.append("  Breathing    : ").append(ansBreathing).append("\n");
            sb.append("  Chills/Dizzy : ").append(ansDizzy).append("\n");
            sb.append("  Daily life   : ").append(ansActivity).append("\n\n");
            sb.append("------------------------------------------------------------\n");
            sb.append("  RESULT       : ").append(severity).append("\n");
            sb.append("------------------------------------------------------------\n\n");
            if (severity.equals("MILD")) {
                sb.append("  RECOMMENDATION: Rest at home. Monitor symptoms.\n");
                sb.append("  If severity increases, re-assess immediately.\n");
            } else if (severity.equals("MODERATE")) {
                sb.append("  RECOMMENDATION: Visit Yirrkala Health Clinic within 24 hours.\n");
                sb.append("  Clinic: Mon–Fri  8:00am – 5:00pm  |  ~2km from community centre\n");
                sb.append("  Phone: (08) 8987 1000\n");
            } else {
                sb.append("  *** EMERGENCY — CALL 000 IMMEDIATELY ***\n");
                sb.append("  Royal Flying Doctor Service: 1800 625 800\n");
                sb.append("  Stay calm. Stay where you are. Have someone with you.\n");
            }
            sb.append("\n============================================================\n");
            sb.append("  This report is generated by SACA (Swinburne University)\n");
            sb.append("  COS70008 Technology Innovation Project — S1 2026\n");
            sb.append("============================================================\n");

            File dl = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS);
            File f  = new File(dl, "SACA_Report_" + ts + ".txt");
            FileWriter w = new FileWriter(f);
            w.write(sb.toString()); w.close();
            Toast.makeText(this, "✓ Report saved to Downloads/SACA_Report_" + ts + ".txt", Toast.LENGTH_LONG).show();
        } catch (Exception e) {
            Toast.makeText(this, "Could not save — check storage permission", Toast.LENGTH_SHORT).show();
        }
    }
}
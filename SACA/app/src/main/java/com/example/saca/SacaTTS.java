package com.example.saca;

import android.content.Context;
import android.speech.tts.TextToSpeech;
import android.util.Log;

import java.util.Locale;

/**
 * SACA TTS — matches desktop tts.py behaviour exactly.
 *
 * Desktop speak() is:
 *  - Non-blocking (queued)
 *  - Drains duplicates (rapid taps don't stack)
 *  - Uses Australian English voice when available
 *  - Rate = slightly fast but clear (Rate 1 in PowerShell SAPI)
 *
 * Usage:
 *   SacaTTS.init(context);          // call once in MainActivity
 *   SacaTTS.speak("Hello");         // call from any activity
 *   SacaTTS.shutdown();             // call in onDestroy of MainActivity
 */
public class SacaTTS {

    private static TextToSpeech tts;
    private static boolean ready = false;
    private static String lastSpoken = "";

    /** Initialise once — call from MainActivity.onCreate() */
    public static void init(Context context) {
        tts = new TextToSpeech(context.getApplicationContext(), status -> {
            if (status == TextToSpeech.SUCCESS) {
                // Prefer Australian English — matches desktop "Karen/en-AU" preference
                int result = tts.setLanguage(new Locale("en", "AU"));
                if (result == TextToSpeech.LANG_MISSING_DATA
                        || result == TextToSpeech.LANG_NOT_SUPPORTED) {
                    // Fall back to default English
                    tts.setLanguage(Locale.ENGLISH);
                }
                // Desktop rate = 1 (slightly fast but clear) — Android 1.1f matches
                tts.setSpeechRate(1.1f);
                tts.setPitch(1.0f);
                ready = true;
                Log.d("SacaTTS", "TTS ready");
            } else {
                Log.e("SacaTTS", "TTS init failed");
            }
        });
    }

    /**
     * Speak text — non-blocking, matches desktop speak().
     * Drains duplicates: rapid repeated taps don't stack up.
     * Pass flush=true to interrupt current speech (for new question).
     */
    public static void speak(String text) {
        speak(text, true);
    }

    public static void speak(String text, boolean flushQueue) {
        if (!ready || tts == null || text == null || text.trim().isEmpty()) return;
        int mode = flushQueue ? TextToSpeech.QUEUE_FLUSH : TextToSpeech.QUEUE_ADD;
        tts.speak(text, mode, null, "saca_" + System.currentTimeMillis());
        lastSpoken = text;
    }

    /** Stop speaking immediately */
    public static void stop() {
        if (tts != null && ready) tts.stop();
    }

    public static boolean isReady() { return ready; }

    /** Call from MainActivity.onDestroy() */
    public static void shutdown() {
        if (tts != null) {
            tts.stop();
            tts.shutdown();
            ready = false;
        }
    }
}

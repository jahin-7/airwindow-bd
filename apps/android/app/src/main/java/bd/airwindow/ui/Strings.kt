package bd.airwindow.ui

import kotlin.math.roundToInt

/** In-app language switch (not the system locale), same wording as the web app. */
class Strings(val bn: Boolean) {
    fun t(en: String, bnText: String) = if (bn) bnText else en

    fun n(x: Double, digits: Int = 0): String = digitsOf(String.format(java.util.Locale.US, "%.${digits}f", x))
    fun n(x: Int): String = digitsOf(x.toString())
    private fun digitsOf(s: String) = if (bn) s.map { if (it in '0'..'9') "০১২৩৪৫৬৭৮৯"[it - '0'] else it }.joinToString("") else s

    /** API times are naive Dhaka wall-clock ISO strings; read the hour directly. */
    fun clock(iso: String): String {
        val h24 = iso.substring(11, 13).toInt()
        val h = if (h24 % 12 == 0) 12 else h24 % 12
        if (!bn) return "$h ${if (h24 < 12) "am" else "pm"}"
        val part = when { h24 < 6 -> "রাত"; h24 < 12 -> "সকাল"; h24 < 15 -> "দুপুর"; h24 < 18 -> "বিকেল"; h24 < 20 -> "সন্ধ্যা"; else -> "রাত" }
        return "$part ${n(h)}টা"
    }

    fun inHours(h: Int) = if (bn) "${n(h)} ঘণ্টা পর" else if (h == 1) "in 1 hour" else "in $h hours"
    fun ago(h: Double) = when {
        h < 1 -> t("less than an hour ago", "এক ঘণ্টার কম আগে")
        else -> t("${h.roundToInt()} hours ago", "${n(h.roundToInt())} ঘণ্টা আগে")
    }
    fun whoMultiple(x: Double) = t("${n(x, 1)}× WHO 24-hour guideline", "WHO ২৪-ঘণ্টা নির্দেশিকার ${n(x, 1)} গুণ")
    fun mean24(x: Double) = t("24-hour average ${n(x)} µg/m³", "২৪ ঘণ্টার গড় ${n(x)} µg/m³")
    fun staleSub(h: Double) = t("Last measurement was ${h.roundToInt()} hours ago. Forecasts are paused until new data arrives.",
        "শেষ পরিমাপ ${n(h.roundToInt())} ঘণ্টা আগে। নতুন তথ্য না আসা পর্যন্ত পূর্বাভাস বন্ধ।")
    fun sensorAt(name: String, m: Double) = if (m < 1000) t("Sensor: $name · ${m.roundToInt()} m from station", "সেন্সর: $name · স্টেশন থেকে ${n(m.roundToInt())} মিটার")
        else t("Sensor: $name · ${n(m / 1000, 1)} km from station", "সেন্সর: $name · স্টেশন থেকে ${n(m / 1000, 1)} কিমি")
    val lowCost get() = t("Low-cost sensor. Readings can differ from the government reference monitors the forecast was trained on.",
        "কম খরচের সেন্সর। পূর্বাভাস যে সরকারি রেফারেন্স মনিটরের তথ্যে প্রশিক্ষিত, তার সঙ্গে এর পাঠ ভিন্ন হতে পারে।")
    fun kmAway(k: Double) = t("${n(k, 1)} km away", "${n(k, 1)} কিমি দূরে")

    val now get() = t("Now", "এখন")
    val today get() = t("Today", "আজ")
    val plan get() = t("Plan", "পরিকল্পনা")
    val stations get() = t("Stations", "স্টেশন")
    val trends get() = t("Trends", "প্রবণতা")
    val more get() = t("More", "আরও")
    val bestWindow get() = t("Lower-pollution window", "তুলনামূলক কম দূষণের সময়")
    val bestNow get() = t("Now is the lowest of the next 6 hours", "আগামী ৬ ঘণ্টার মধ্যে এখনই সবচেয়ে কম")
    val noWindow get() = t("No forecast available right now", "এই মুহূর্তে কোনো পূর্বাভাস নেই")
    val loading get() = t("Loading…", "লোড হচ্ছে…")
    val measured get() = t("Measured", "মাপা")
    val forecast get() = t("Forecast", "পূর্বাভাস")
    val range get() = t("likely range (80%)", "সম্ভাব্য সীমা (৮০%)")
    val source get() = t("Source", "উৎস")
    val stale get() = t("This reading is out of date", "এই তথ্য পুরনো")
    val noData get() = t("No current observation available for this area", "এই এলাকার কোনো বর্তমান পরিমাপ নেই")
    val noDataSub get() = t("We don't show estimates where there is no recent measurement.", "সাম্প্রতিক পরিমাপ না থাকলে আমরা অনুমান দেখাই না।")
    val replayTitle get() = t("Demo mode: historical data", "ডেমো মোড: পুরনো তথ্য")
    val replaySub get() = t("No live feed is connected. You are seeing CAMS-BD measurements from this date and hour in 2024, not today's air.",
        "কোনো লাইভ উৎস যুক্ত নেই। আপনি ২০২৪ সালের এই তারিখ ও সময়ের CAMS-BD পরিমাপ দেখছেন, আজকের বাতাস নয়।")
    val nextHours get() = t("Next hours", "আগামী ঘণ্টাগুলো")
    val aqiNeeds get() = t("Needs 18+ hours of readings in the last day", "গত এক দিনে অন্তত ১৮ ঘণ্টার পরিমাপ দরকার")
    val notSafety get() = t("Ranking compares these hours only. Lower is not a guarantee of safe air. Follow official advisories.",
        "শুধু এই ঘণ্টাগুলোর তুলনা। কম মানেই নিরাপদ বাতাস নয়। সরকারি পরামর্শ মেনে চলুন।")
    val planTitle get() = t("Plan an activity", "কাজের পরিকল্পনা")
    val tagline get() = t("Choose a better time to be outdoors", "বাইরে যাওয়ার জন্য তুলনামূলক ভালো সময় বেছে নিন")
    val activity get() = t("Activity", "কাজ")
    val pollutant get() = t("Pollutant", "দূষক")
    val ranked get() = t("Hours ranked by predicted PM", "পূর্বাভাসিত PM অনুযায়ী ঘণ্টার ক্রম")
    val overlap get() = t("Ranges overlap: the difference may not be real", "সীমা মিলে যাচ্ছে: পার্থক্য নিশ্চিত নয়")
    val clearlyLower get() = t("Clearly lower than the next", "পরেরটির চেয়ে স্পষ্টভাবে কম")
    val coverage get() = t("Values apply near each station only. We do not fill in the space between stations.",
        "মান শুধু প্রতিটি স্টেশনের কাছাকাছি প্রযোজ্য। স্টেশনের মাঝের জায়গা আমরা অনুমান করি না।")
    val useLocation get() = t("Use my location", "আমার অবস্থান ব্যবহার করুন")
    val locationNote get() = t("Optional. Your location stays on this device.", "ঐচ্ছিক। আপনার অবস্থান এই ডিভাইসেই থাকে।")
    val search get() = t("Search city or station", "শহর বা স্টেশন খুঁজুন")
    val daily get() = t("Daily average · µg/m³", "দৈনিক গড় · µg/m³")
    val historical get() = t("Historical CAMS-BD measurements (2024).", "CAMS-BD এর পুরনো পরিমাপ (২০২৪)।")
    val days7 get() = t("7 days", "৭ দিন")
    val days30 get() = t("30 days", "৩০ দিন")
    val trendNote get() = t("Days with fewer than 18 hourly readings are left blank. Dashed line: WHO 24-hour guideline.",
        "যেদিন ১৮ ঘণ্টার কম পরিমাপ আছে সেদিনের গড় দেখানো হয়নি। ড্যাশ লাইন: WHO ২৪-ঘণ্টা নির্দেশিকা।")
    val settings get() = t("Settings", "সেটিংস")
    val language get() = t("Language", "ভাষা")
    val scale get() = t("Number style", "সংখ্যার ধরন")
    val scaleDoe get() = t("Bangladesh AQI (DoE bands)", "বাংলাদেশ AQI (পরিবেশ অধিদপ্তরের স্তর)")
    val scaleEpa get() = t("US EPA AQI", "US EPA AQI")
    val scaleUg get() = t("µg/m³ only", "শুধু µg/m³")
    val theme get() = t("Theme", "থিম")
    val system get() = t("System", "সিস্টেম")
    val light get() = t("Light", "হালকা")
    val dark get() = t("Dark", "গাঢ়")
    val lowData get() = t("Low-data mode", "কম ডেটা মোড")
    val method get() = t("Data & methodology", "তথ্য ও পদ্ধতি")
    val methodText get() = t(
        "Training data: CAMS-BD — hourly measurements from Bangladesh DoE Continuous Air Monitoring Stations, Nov 2012–Jan 2025 (CC BY 4.0). Weather: Open-Meteo.\n\nAQI: bands and colours from DoE's \"AQI Scheme for Bangladesh\"; concentration-to-index uses US EPA (2024) breakpoints on 24-hour means. WHO 2021 guideline: PM2.5 15, PM10 45 µg/m³ (24-hour).\n\nThis is not medical advice. During severe pollution, follow official public-health advisories.",
        "মডেল প্রশিক্ষণ: CAMS-BD — বাংলাদেশ পরিবেশ অধিদপ্তরের ক্রমাগত বায়ু পর্যবেক্ষণ স্টেশনের ঘণ্টাভিত্তিক পরিমাপ, নভেম্বর ২০১২–জানুয়ারি ২০২৫ (CC BY 4.0)। আবহাওয়া: Open-Meteo।\n\nAQI: পরিবেশ অধিদপ্তরের \"AQI Scheme for Bangladesh\" স্তর ও রং। ঘনত্ব থেকে সূচক রূপান্তরে US EPA (২০২৪) ব্রেকপয়েন্ট, ২৪-ঘণ্টা গড়ে। WHO ২০২১ নির্দেশিকা: PM2.5 ১৫, PM10 ৪৫ µg/m³ (২৪ ঘণ্টা)।\n\nএটি চিকিৎসা পরামর্শ নয়। তীব্র দূষণের সময় সরকারি স্বাস্থ্য পরামর্শ মেনে চলুন।")
    val deleteAll get() = t("Delete my preferences", "আমার পছন্দগুলো মুছুন")
    val retry get() = t("Try again", "আবার চেষ্টা করুন")
    val errorGeneric get() = t("Couldn't reach the AirWindow server.", "এয়ারউইন্ডো সার্ভারে পৌঁছানো যায়নি।")
    val chooseLang get() = t("Choose your language", "আপনার ভাষা বেছে নিন")
    val chooseLangSub get() = t("You can change this any time in Settings.", "সেটিংসে গিয়ে যেকোনো সময় বদলাতে পারবেন।")
    val cont get() = t("Continue", "এগিয়ে যান")

    fun act(key: String) = when (key) {
        "walk" -> t("Walk", "হাঁটা"); "exercise" -> t("Exercise", "ব্যায়াম"); "commute" -> t("Commute", "যাতায়াত")
        "school_run" -> t("School run", "স্কুলে আনা-নেওয়া"); else -> t("Errands", "কেনাকাটা")
    }
}

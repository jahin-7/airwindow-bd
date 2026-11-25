package bd.airwindow

import bd.airwindow.data.Latest
import bd.airwindow.data.WindowsResponse
import bd.airwindow.ui.Strings
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Test

class StringsAndModelsTest {
    private val en = Strings(bn = false)
    private val bn = Strings(bn = true)
    private val json = Json { ignoreUnknownKeys = true }

    @Test fun banglaDigits() {
        assertEquals("১০৪", bn.n(104.1))
        assertEquals("১৫.০", bn.n(15.0, 1))
        assertEquals("104", en.n(104.1))
    }

    @Test fun clockReadsDhakaWallTimeWithoutConversion() {
        assertEquals("4 pm", en.clock("2024-11-25T16:00:00"))
        assertEquals("12 am", en.clock("2024-11-26T00:00:00"))
        assertEquals("বিকেল ৪টা", bn.clock("2024-11-25T16:00:00"))
        assertEquals("সকাল ৯টা", bn.clock("2024-11-25T09:00:00"))
    }

    @Test fun parsesLatestReplayResponse() {
        val raw = """{"station":{"id":"dhk_darussalam","name":"Dhaka – Darussalam","name_bn":"ঢাকা – দারুস সালাম","city":"Dhaka","lat":23.781,"lon":90.356},
            "mode":"replay","status":"ok","observed_at":"2024-11-25T15:00:00","age_hours":0.0,"source":"CAMS-BD historical replay (2024)",
            "is_live":false,"provider_location":null,"readings":{"pm25":{"value":104.1,"unit":"µg/m³","observed_at":"2024-11-25T15:00:00",
            "aqi_24h":{"pollutant":"pm25","aqi":301,"band":"hazardous","label_en":"Hazardous","label_bn":"বিপজ্জনক","color":"#7F0000",
            "mean_24h":225.7,"hours_used":24,"who_multiple":15.0,"method":"x"},"who_24h_guideline":15.0}}}"""
        val l = json.decodeFromString<Latest>(raw)
        assertFalse(l.isLive!!)
        assertEquals(301, l.readings["pm25"]!!.aqi24h!!.aqi)
    }

    @Test fun measuredNowHasNoInterval() {
        val raw = """{"issued_at":"2024-11-25T15:00:00","model_version":"lgb","mode":"replay","is_live":false,"note":"n",
            "windows":[{"valid_at":"2024-11-25T15:00:00","horizon_h":0,"value":104.1,"lo80":null,"hi80":null,"kind":"measured",
            "relative_to_best_pct":9.0,"rank":2,"clearly_lower_than_next":false}]}"""
        val w = json.decodeFromString<WindowsResponse>(raw).windows.single()
        assertEquals("measured", w.kind)
        assertNull(w.lo80)
    }
}

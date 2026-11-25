package bd.airwindow.data

import bd.airwindow.BuildConfig
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.concurrent.TimeUnit

// Mirrors services/api responses. Times are naive Asia/Dhaka wall-clock ISO strings.

@Serializable
data class Station(
    val id: String, val name: String, @SerialName("name_bn") val nameBn: String, val city: String,
    val lat: Double, val lon: Double, @SerialName("distance_km") val distanceKm: Double? = null,
)

@Serializable
data class Aqi24h(
    val aqi: Int, val band: String, @SerialName("label_en") val labelEn: String, @SerialName("label_bn") val labelBn: String,
    val color: String, @SerialName("mean_24h") val mean24h: Double, @SerialName("hours_used") val hoursUsed: Int,
    @SerialName("who_multiple") val whoMultiple: Double,
)

@Serializable
data class Reading(
    val value: Double, val unit: String, @SerialName("observed_at") val observedAt: String,
    @SerialName("aqi_24h") val aqi24h: Aqi24h? = null,
)

@Serializable
data class Latest(
    val station: Station, val mode: String, val status: String, val message: String? = null,
    @SerialName("observed_at") val observedAt: String? = null, @SerialName("age_hours") val ageHours: Double? = null,
    val source: String? = null, @SerialName("is_live") val isLive: Boolean? = null,
    val readings: Map<String, Reading> = emptyMap(),
)

@Serializable
data class HourWindow(
    @SerialName("valid_at") val validAt: String, @SerialName("horizon_h") val horizonH: Int, val value: Double,
    val lo80: Double? = null, val hi80: Double? = null, val kind: String, val rank: Int,
    @SerialName("clearly_lower_than_next") val clearlyLowerThanNext: Boolean = false,
)

@Serializable
data class WindowsResponse(
    @SerialName("issued_at") val issuedAt: String, @SerialName("model_version") val modelVersion: String,
    val mode: String, @SerialName("is_live") val isLive: Boolean, val windows: List<HourWindow>, val note: String,
)

@Serializable
data class Meta(val mode: String, @SerialName("replay_note") val replayNote: String? = null)

@Serializable
data class DailyPoint(val date: String, @SerialName("pm25_mean") val pm25: Double? = null, @SerialName("pm10_mean") val pm10: Double? = null)

@Serializable
data class Trends(val daily: List<DailyPoint>, val source: String)

@Serializable
private data class WindowsRequest(
    @SerialName("station_id") val stationId: String, val pollutant: String, val activity: String,
    @SerialName("duration_min") val durationMin: Int = 60,
)

class ApiException(val code: Int, message: String) : Exception(message)

object Api {
    private val json = Json { ignoreUnknownKeys = true }
    private val http = OkHttpClient.Builder().connectTimeout(8, TimeUnit.SECONDS).readTimeout(20, TimeUnit.SECONDS).build()
    private val base = BuildConfig.API_BASE_URL.trimEnd('/')

    private suspend fun get(path: String): String = withContext(Dispatchers.IO) {
        exec(Request.Builder().url("$base$path").build())
    }

    private suspend fun post(path: String, body: String): String = withContext(Dispatchers.IO) {
        exec(Request.Builder().url("$base$path").post(body.toRequestBody("application/json".toMediaType())).build())
    }

    private fun exec(req: Request): String = http.newCall(req).execute().use { r ->
        val text = r.body?.string().orEmpty()
        if (!r.isSuccessful) {
            val detail = runCatching { json.parseToJsonElement(text).jsonObject["detail"]?.jsonPrimitive?.content }.getOrNull()
            throw ApiException(r.code, detail ?: "HTTP ${r.code}")
        }
        text
    }

    suspend fun meta(): Meta = json.decodeFromString(get("/api/meta"))
    suspend fun locations(): List<Station> = json.decodeFromString(get("/api/locations"))
    suspend fun nearby(lat: Double, lon: Double): List<Station> = json.decodeFromString(get("/api/stations/nearby?lat=$lat&lon=$lon"))
    suspend fun latest(id: String): Latest = json.decodeFromString(get("/api/observations/latest?station_id=$id"))
    suspend fun trends(id: String, days: Int): Trends = json.decodeFromString(get("/api/trends?station_id=$id&days=$days"))
    suspend fun windows(id: String, pollutant: String, activity: String): WindowsResponse =
        json.decodeFromString(post("/api/activity-windows", json.encodeToString(WindowsRequest(id, pollutant, activity))))
}

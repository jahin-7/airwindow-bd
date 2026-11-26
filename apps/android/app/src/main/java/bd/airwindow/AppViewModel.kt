package bd.airwindow

import android.app.Application
import android.os.SystemClock
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import bd.airwindow.data.Api
import bd.airwindow.data.ApiException
import bd.airwindow.data.Latest
import bd.airwindow.data.Meta
import bd.airwindow.data.PrefsRepo
import bd.airwindow.data.Station
import bd.airwindow.data.Trends
import bd.airwindow.data.UserPrefs
import bd.airwindow.data.WindowsResponse
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

/** Result of a network call that can be loading, ok, or failed with a user-facing message. */
sealed interface Load<out T> {
    data object Loading : Load<Nothing>
    data class Ok<T>(val value: T) : Load<T>
    data class Err(val message: String?, val offline: Boolean) : Load<Nothing>
}

private suspend fun <T> load(block: suspend () -> T): Load<T> = try {
    Load.Ok(block())
} catch (e: ApiException) {
    Load.Err(e.message, offline = false)
} catch (e: Exception) {
    Load.Err(null, offline = true)
}

class AppViewModel(app: Application) : AndroidViewModel(app) {
    private val repo = PrefsRepo(app)
    val prefs: StateFlow<UserPrefs?> = repo.prefs.stateIn(viewModelScope, SharingStarted.Eagerly, null)

    val meta = MutableStateFlow<Meta?>(null)
    val latest = MutableStateFlow<Load<Latest>>(Load.Loading)
    /** Today and Plan rank hours for different activities, so each keeps its own copy. */
    val todayWindows = MutableStateFlow<Load<WindowsResponse>>(Load.Loading)
    val planWindows = MutableStateFlow<Load<WindowsResponse>>(Load.Loading)
    val stations = MutableStateFlow<Load<List<Station>>>(Load.Loading)
    val trends = MutableStateFlow<Load<Trends>>(Load.Loading)

    /** What each flow last asked for, and when. */
    private val asked = mutableMapOf<MutableStateFlow<*>, Pair<Any, Long>>()

    init {
        viewModelScope.launch { meta.value = runCatching { Api.meta() }.getOrNull() }
    }

    /**
     * Loads [key] into this flow. Coming back to a tab with the same key keeps what's on screen
     * (and skips the call if it's under a minute old) instead of flashing a placeholder, which made
     * the page jump and lose its scroll position. A failed refresh doesn't wipe good data either.
     */
    private fun <T> MutableStateFlow<Load<T>>.fetch(key: Any, force: Boolean = false, keepShown: Boolean = false, block: suspend () -> T) = viewModelScope.launch {
        val flow = this@fetch
        val prev = asked[flow]
        val now = SystemClock.elapsedRealtime()
        val same = prev?.first == key
        val shown = flow.value is Load.Ok
        if (same && shown && !force && now - prev!!.second < 60_000) return@launch
        if (!shown || (!same && !keepShown)) flow.value = Load.Loading
        asked[flow] = key to now
        val r = load(block)
        if (asked[flow]?.first != key) return@launch // a newer request took over
        if (r is Load.Err && same && shown) return@launch
        flow.value = r
    }

    fun update(f: (UserPrefs) -> UserPrefs) = viewModelScope.launch {
        repo.update(f, prefs.value ?: UserPrefs())
    }

    fun clearPrefs() = viewModelScope.launch { repo.clear() }

    fun refreshToday(p: UserPrefs, force: Boolean = false) {
        latest.fetch(p.stationId, force) { Api.latest(p.stationId) }
        todayWindows.fetch(Triple(p.stationId, p.pollutant, "walk"), force) { Api.windows(p.stationId, p.pollutant, "walk") }
    }

    fun refreshPlan(p: UserPrefs, activity: String, force: Boolean = false) {
        // Switching activity re-ranks the same hours: keep the list up until the new order arrives.
        val prev = asked[planWindows]?.first as? Triple<*, *, *>
        val sameHours = prev?.first == p.stationId && prev.second == p.pollutant
        planWindows.fetch(Triple(p.stationId, p.pollutant, activity), force, keepShown = sameHours) { Api.windows(p.stationId, p.pollutant, activity) }
    }

    fun loadStations(lat: Double? = null, lon: Double? = null) =
        stations.fetch(if (lat != null && lon != null) lat to lon else "all", force = lat != null) {
            if (lat != null && lon != null) Api.nearby(lat, lon) else Api.locations()
        }

    fun loadTrends(id: String, days: Int) = trends.fetch(id to days) { Api.trends(id, days) }
}

package bd.airwindow

import android.app.Application
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
    val windows = MutableStateFlow<Load<WindowsResponse>>(Load.Loading)
    val stations = MutableStateFlow<Load<List<Station>>>(Load.Loading)
    val trends = MutableStateFlow<Load<Trends>>(Load.Loading)

    init {
        viewModelScope.launch { meta.value = runCatching { Api.meta() }.getOrNull() }
    }

    fun update(f: (UserPrefs) -> UserPrefs) = viewModelScope.launch {
        repo.update(f, prefs.value ?: UserPrefs())
    }

    fun clearPrefs() = viewModelScope.launch { repo.clear() }

    fun refreshToday(p: UserPrefs, activity: String = "walk") = viewModelScope.launch {
        latest.value = Load.Loading
        windows.value = Load.Loading
        latest.value = load { Api.latest(p.stationId) }
        windows.value = load { Api.windows(p.stationId, p.pollutant, activity) }
    }

    fun refreshWindows(p: UserPrefs, activity: String) = viewModelScope.launch {
        windows.value = Load.Loading
        windows.value = load { Api.windows(p.stationId, p.pollutant, activity) }
    }

    fun loadStations(lat: Double? = null, lon: Double? = null) = viewModelScope.launch {
        stations.value = load { if (lat != null && lon != null) Api.nearby(lat, lon) else Api.locations() }
    }

    fun loadTrends(id: String, days: Int) = viewModelScope.launch {
        trends.value = Load.Loading
        trends.value = load { Api.trends(id, days) }
    }
}

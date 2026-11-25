package bd.airwindow.data

import android.content.Context
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

/** On-device only; no account. Mirrors the web app's preferences. */
data class UserPrefs(
    val lang: String? = null,          // null until chosen on first open
    val stationId: String = "dhk_darussalam",
    val scale: String = "doe",         // doe | epa | ugm3
    val pollutant: String = "pm25",
    val theme: String = "system",      // system | light | dark
    val lowData: Boolean = false,
)

private val Context.store by preferencesDataStore("airwindow_prefs")

class PrefsRepo(private val ctx: Context) {
    private object K {
        val lang = stringPreferencesKey("lang")
        val station = stringPreferencesKey("station")
        val scale = stringPreferencesKey("scale")
        val pollutant = stringPreferencesKey("pollutant")
        val theme = stringPreferencesKey("theme")
        val lowData = booleanPreferencesKey("low_data")
    }

    val prefs: Flow<UserPrefs> = ctx.store.data.map { p: Preferences ->
        val d = UserPrefs()
        UserPrefs(p[K.lang], p[K.station] ?: d.stationId, p[K.scale] ?: d.scale, p[K.pollutant] ?: d.pollutant,
            p[K.theme] ?: d.theme, p[K.lowData] ?: d.lowData)
    }

    suspend fun update(f: (UserPrefs) -> UserPrefs, current: UserPrefs) {
        val n = f(current)
        ctx.store.edit { p ->
            n.lang?.let { p[K.lang] = it } ?: p.remove(K.lang)
            p[K.station] = n.stationId; p[K.scale] = n.scale; p[K.pollutant] = n.pollutant
            p[K.theme] = n.theme; p[K.lowData] = n.lowData
        }
    }

    suspend fun clear() = ctx.store.edit { it.clear() }
}

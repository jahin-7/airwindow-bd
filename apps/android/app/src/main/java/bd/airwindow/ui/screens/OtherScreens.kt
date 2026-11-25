package bd.airwindow.ui.screens

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.location.LocationManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import bd.airwindow.AppViewModel
import bd.airwindow.Load
import bd.airwindow.data.UserPrefs
import bd.airwindow.ui.AwCard
import bd.airwindow.ui.OneUiScreen
import bd.airwindow.ui.SectionLabel
import bd.airwindow.ui.Segmented
import bd.airwindow.ui.Strings
import bd.airwindow.ui.theme.LocalAw

@Composable
fun StationsScreen(vm: AppViewModel, p: UserPrefs, s: Strings, picked: () -> Unit) {
    val c = LocalAw.current
    val ctx = LocalContext.current
    LaunchedEffect(Unit) { vm.loadStations() }
    val list by vm.stations.collectAsState()
    var q by rememberSaveable { mutableStateOf("") }
    var locErr by remember { mutableStateOf(false) }
    val perm = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { ok ->
        val loc = if (ok) lastLocation(ctx) else null
        if (loc != null) vm.loadStations(loc.first, loc.second) else locErr = true
    }

    OneUiScreen(s.stations, sub = { Text(s.coverage, color = c.ink2, fontSize = 15.sp) }) {
        item {
            BasicTextField(q, { q = it }, singleLine = true, textStyle = TextStyle(color = c.ink, fontSize = 16.sp),
                cursorBrush = SolidColor(c.accent),
                modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(50)).background(c.card).padding(horizontal = 20.dp, vertical = 14.dp),
                decorationBox = { inner -> if (q.isEmpty()) Text(s.search, color = c.ink3, fontSize = 16.sp); inner() })
        }
        item {
            AwCard(tone = "accent", onClick = { locErr = false; perm.launch(Manifest.permission.ACCESS_COARSE_LOCATION) }) {
                Text("◎  ${s.useLocation}", fontWeight = FontWeight.SemiBold)
                Text(s.locationNote, fontSize = 12.sp, color = c.ink2)
            }
        }
        if (locErr) item { Text(s.t("Couldn't get your location. Pick from the list instead.", "অবস্থান পাওয়া যায়নি। তালিকা থেকে বেছে নিন।"), color = c.warn, fontSize = 13.sp) }
        when (val l = list) {
            is Load.Ok -> item {
                val shown = l.value.filter { q.isBlank() || it.name.contains(q, true) || it.city.contains(q, true) || it.nameBn.contains(q.trim()) }
                AwCard {
                    shown.forEachIndexed { i, st ->
                        if (i > 0) HorizontalDivider(color = c.line)
                        Row(Modifier.fillMaxWidth().clickable { vm.update { it.copy(stationId = st.id) }; picked() }.padding(vertical = 14.dp),
                            verticalAlignment = Alignment.CenterVertically) {
                            Box(Modifier.size(12.dp).clip(CircleShape).then(
                                if (st.id == p.stationId) Modifier.background(c.accent) else Modifier.border(2.dp, c.line, CircleShape)))
                            Spacer(Modifier.width(12.dp))
                            Column(Modifier.weight(1f)) {
                                Text(if (s.bn) st.nameBn else st.name, fontWeight = FontWeight.Medium)
                                Text(st.distanceKm?.let { s.kmAway(it) } ?: st.city, fontSize = 13.sp, color = c.ink2)
                            }
                            Text("›", color = c.ink3)
                        }
                    }
                }
            }
            is Load.Err -> item { AwCard(tone = "warn") { Text(l.message ?: s.errorGeneric) } }
            Load.Loading -> item { AwCard { Box(Modifier.height(200.dp)) } }
        }
    }
}

@SuppressLint("MissingPermission") // only called after the permission is granted
private fun lastLocation(ctx: Context): Pair<Double, Double>? {
    val lm = ctx.getSystemService(Context.LOCATION_SERVICE) as LocationManager
    return lm.getProviders(true).mapNotNull { runCatching { lm.getLastKnownLocation(it) }.getOrNull() }
        .maxByOrNull { it.time }?.let { it.latitude to it.longitude }
}

@Composable
fun TrendsScreen(vm: AppViewModel, p: UserPrefs, s: Strings) {
    val c = LocalAw.current
    var days by rememberSaveable { mutableStateOf(7) }
    LaunchedEffect(p.stationId, days) { vm.loadTrends(p.stationId, days) }
    val tr by vm.trends.collectAsState()
    val who = if (p.pollutant == "pm25") 15.0 else 45.0

    OneUiScreen(s.trends, sub = { Text(s.historical, color = c.ink2, fontSize = 15.sp) }) {
        item { Segmented(days, listOf(7 to s.days7, 30 to s.days30)) { days = it } }
        item { Segmented(p.pollutant, listOf("pm25" to "PM2.5", "pm10" to "PM10")) { v -> vm.update { it.copy(pollutant = v) } } }
        item {
            AwCard {
                Text(s.daily, fontSize = 13.sp, color = c.ink3, fontWeight = FontWeight.Medium)
                Spacer(Modifier.height(12.dp))
                when (val t = tr) {
                    is Load.Ok -> {
                        val vals = t.value.daily.map { if (p.pollutant == "pm25") it.pm25 else it.pm10 }
                        val max = ((vals.filterNotNull().maxOrNull() ?: who).coerceAtLeast(who) * 1.1).toFloat()
                        Canvas(Modifier.fillMaxWidth().height(220.dp).semantics {
                            contentDescription = t.value.daily.joinToString { "${it.date}: ${(if (p.pollutant == "pm25") it.pm25 else it.pm10) ?: "–"}" }
                        }) {
                            val n = vals.size.coerceAtLeast(1)
                            val slot = size.width / n
                            val bw = (slot * 0.6f).coerceAtMost(28.dp.toPx())
                            vals.forEachIndexed { i, v ->
                                if (v == null) return@forEachIndexed
                                val h = (v.toFloat() / max) * size.height
                                drawRoundRect(c.ink, Offset(i * slot + (slot - bw) / 2, size.height - h), Size(bw, h), CornerRadius(8.dp.toPx()))
                            }
                            val y = size.height - (who.toFloat() / max) * size.height
                            drawLine(c.ink2, Offset(0f, y), Offset(size.width, y), 1.5.dp.toPx(),
                                pathEffect = PathEffect.dashPathEffect(floatArrayOf(10f, 10f)))
                        }
                        Spacer(Modifier.height(8.dp))
                        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            t.value.daily.firstOrNull()?.let { Text(s.n(it.date.substring(8).toInt()) + "/" + s.n(it.date.substring(5, 7).toInt()), fontSize = 11.sp, color = c.ink3) }
                            t.value.daily.lastOrNull()?.let { Text(s.n(it.date.substring(8).toInt()) + "/" + s.n(it.date.substring(5, 7).toInt()), fontSize = 11.sp, color = c.ink3) }
                        }
                    }
                    is Load.Err -> Text(t.message ?: s.errorGeneric, color = c.ink2)
                    Load.Loading -> Box(Modifier.height(220.dp))
                }
                Spacer(Modifier.height(12.dp))
                Text(s.trendNote, fontSize = 12.sp, color = c.ink3)
            }
        }
    }
}

@Composable
fun MoreScreen(vm: AppViewModel, p: UserPrefs, s: Strings) {
    val c = LocalAw.current
    OneUiScreen(s.more) {
        item { SectionLabel(s.settings) }
        item {
            AwCard {
                Text(s.language, fontSize = 13.sp, color = c.ink3, fontWeight = FontWeight.Medium)
                Spacer(Modifier.height(8.dp))
                Segmented(p.lang ?: "en", listOf("bn" to "বাংলা", "en" to "English")) { v -> vm.update { it.copy(lang = v) } }
                Spacer(Modifier.height(18.dp))
                Text(s.scale, fontSize = 13.sp, color = c.ink3, fontWeight = FontWeight.Medium)
                listOf("doe" to s.scaleDoe, "epa" to s.scaleEpa, "ugm3" to s.scaleUg).forEach { (v, label) ->
                    Row(Modifier.fillMaxWidth().clickable { vm.update { it.copy(scale = v) } }.padding(vertical = 12.dp),
                        verticalAlignment = Alignment.CenterVertically) {
                        Text(label, Modifier.weight(1f))
                        Box(Modifier.size(20.dp).clip(CircleShape).border(if (p.scale == v) 6.dp else 2.dp, if (p.scale == v) c.accent else c.line, CircleShape))
                    }
                }
                Spacer(Modifier.height(10.dp))
                Text(s.theme, fontSize = 13.sp, color = c.ink3, fontWeight = FontWeight.Medium)
                Spacer(Modifier.height(8.dp))
                Segmented(p.theme, listOf("system" to s.system, "light" to s.light, "dark" to s.dark)) { v -> vm.update { it.copy(theme = v) } }
                Row(Modifier.fillMaxWidth().padding(top = 14.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text(s.lowData, Modifier.weight(1f))
                    Switch(p.lowData, { v -> vm.update { it.copy(lowData = v) } },
                        colors = SwitchDefaults.colors(checkedTrackColor = c.accentFill, uncheckedThumbColor = c.ink3, uncheckedTrackColor = c.card2, uncheckedBorderColor = c.ink3))
                }
            }
        }
        item { SectionLabel(s.method) }
        item { AwCard { Text(s.methodText, fontSize = 14.sp, lineHeight = 21.sp) } }
        item {
            Box(Modifier.fillMaxWidth().clip(RoundedCornerShape(50)).background(c.card).clickable { vm.clearPrefs() }.padding(vertical = 16.dp),
                contentAlignment = Alignment.Center) { Text(s.deleteAll, color = c.warn, fontWeight = FontWeight.SemiBold) }
        }
    }
}

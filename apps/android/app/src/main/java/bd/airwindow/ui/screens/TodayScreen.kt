package bd.airwindow.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import bd.airwindow.AppViewModel
import bd.airwindow.Load
import bd.airwindow.data.Reading
import bd.airwindow.data.UserPrefs
import bd.airwindow.ui.AwCard
import bd.airwindow.ui.HoursStrip
import bd.airwindow.ui.KindTag
import bd.airwindow.ui.OneUiScreen
import bd.airwindow.ui.ReplayBanner
import bd.airwindow.ui.SectionLabel
import bd.airwindow.ui.Strings
import bd.airwindow.ui.hexColor
import bd.airwindow.ui.theme.LocalAw

@Composable
fun TodayScreen(vm: AppViewModel, p: UserPrefs, s: Strings, openStations: () -> Unit, openPlan: () -> Unit) {
    val c = LocalAw.current
    LaunchedEffect(p.stationId, p.pollutant) { vm.refreshToday(p) }
    val latest by vm.latest.collectAsState()
    val win by vm.windows.collectAsState()
    val meta by vm.meta.collectAsState()

    val best = (win as? Load.Ok)?.value?.windows?.firstOrNull { it.rank == 1 }
    val title = when {
        win is Load.Loading -> s.loading
        best == null -> s.noWindow
        best.horizonH == 0 -> s.bestNow
        else -> "${s.clock(best.validAt)} · ${s.inHours(best.horizonH)}"
    }
    val st = (latest as? Load.Ok)?.value?.station
    OneUiScreen(title, sub = {
        Row(Modifier.clip(RoundedCornerShape(50)).background(c.card).clickable(onClick = openStations).padding(horizontal = 12.dp, vertical = 6.dp),
            verticalAlignment = Alignment.CenterVertically) {
            Text("● ", color = c.accent, fontSize = 12.sp)
            Text("${s.bestWindow} · ${st?.let { if (s.bn) it.nameBn else it.name } ?: "…"} ›", fontSize = 14.sp, color = c.ink)
        }
    }) {
        if (meta?.mode == "replay") item { ReplayBanner(s) }
        when (val l = latest) {
            is Load.Err -> item {
                AwCard(tone = "warn") {
                    Text(if (l.offline) s.errorGeneric else l.message ?: s.errorGeneric)
                    Spacer(Modifier.height(12.dp))
                    Text(s.retry, color = c.accentFill, fontWeight = FontWeight.SemiBold, modifier = Modifier.clickable { vm.refreshToday(p) })
                }
            }
            is Load.Ok -> {
                val v = l.value
                if (v.status == "no_data") item { AwCard(tone = "warn") { Text(s.noData, fontWeight = FontWeight.SemiBold); Text(s.noDataSub, color = c.ink2, fontSize = 14.sp) } }
                if (v.status == "stale") item { AwCard(tone = "warn") { Text(s.stale, fontWeight = FontWeight.SemiBold); Text(s.staleSub(v.ageHours ?: 0.0), color = c.ink2, fontSize = 14.sp) } }
                v.readings[p.pollutant]?.let { r -> item { MeasuredCard(r, p, s, v.source ?: "", v.ageHours ?: 0.0, v.readings["pm10"]?.value) {
                    if (v.providerLocation != null && v.providerDistanceM != null)
                        Text(s.sensorAt(v.providerLocation, v.providerDistanceM), fontSize = 12.sp, color = LocalAw.current.ink3)
                    if (v.sensorGrade == "low_cost") Text(s.lowCost, fontSize = 12.sp, color = LocalAw.current.warn)
                } } }
            }
            Load.Loading -> item { AwCard { Box(Modifier.height(160.dp)) } }
        }
        item { SectionLabel(s.nextHours) }
        item {
            AwCard {
                when (val w = win) {
                    is Load.Ok -> {
                        HoursStrip(w.value.windows, s)
                        Spacer(Modifier.height(12.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) { KindTag(true, s.measured); KindTag(false, s.forecast) }
                        Spacer(Modifier.height(4.dp))
                        Text(s.range, fontSize = 12.sp, color = c.ink3)
                        Spacer(Modifier.height(12.dp))
                        Text(s.notSafety, fontSize = 12.sp, color = c.ink3, lineHeight = 17.sp)
                    }
                    is Load.Err -> Text(w.message ?: s.errorGeneric, color = c.ink2, fontSize = 14.sp)
                    Load.Loading -> Box(Modifier.height(200.dp))
                }
            }
        }
        item {
            AwCard(tone = "accent", onClick = openPlan) {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(s.planTitle, style = MaterialTheme.typography.titleMedium)
                    Text("›", color = c.accent, style = MaterialTheme.typography.titleMedium)
                }
            }
        }
    }
}

@Composable
private fun MeasuredCard(r: Reading, p: UserPrefs, s: Strings, source: String, ageH: Double, pm10: Double?, footer: @Composable () -> Unit = {}) {
    val c = LocalAw.current
    AwCard {
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            KindTag(true, "${s.measured} · ${if (p.pollutant == "pm25") "PM2.5" else "PM10"}")
            Text(s.clock(r.observedAt), fontSize = 12.sp, color = c.ink3)
        }
        Row(verticalAlignment = Alignment.Bottom) {
            Text(s.n(r.value), style = MaterialTheme.typography.headlineLarge)
            Spacer(Modifier.width(8.dp))
            Text("µg/m³", color = c.ink2, fontSize = 17.sp, modifier = Modifier.padding(bottom = 10.dp))
        }
        if (p.scale != "ugm3") {
            val a = r.aqi24h
            Spacer(Modifier.height(12.dp))
            if (a == null) Text(s.aqiNeeds, fontSize = 13.sp, color = c.ink3)
            else Row(verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.width(8.dp).height(44.dp).clip(RoundedCornerShape(50)).background(hexColor(a.color)))
                Spacer(Modifier.width(12.dp))
                Column {
                    Text("${if (p.scale == "doe") "AQI" else "US AQI"} ${s.n(a.aqi)} · ${if (s.bn) a.labelBn else a.labelEn}", fontWeight = FontWeight.SemiBold)
                    Text(s.mean24(a.mean24h), fontSize = 13.sp, color = c.ink2)
                    Text(s.whoMultiple(a.whoMultiple), fontSize = 13.sp, color = c.ink2)
                }
            }
        }
        Spacer(Modifier.height(12.dp))
        HorizontalDivider(color = c.line)
        Spacer(Modifier.height(8.dp))
        Text("${s.source}: $source · ${s.ago(ageH)}${if (pm10 != null && p.pollutant == "pm25") " · PM10 ${s.n(pm10)} µg/m³" else ""}",
            fontSize = 12.sp, color = c.ink3)
        footer()
    }
}

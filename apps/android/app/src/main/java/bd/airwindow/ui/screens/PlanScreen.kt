package bd.airwindow.ui.screens

import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import bd.airwindow.AppViewModel
import bd.airwindow.Load
import bd.airwindow.data.UserPrefs
import bd.airwindow.ui.AwCard
import bd.airwindow.ui.Chip
import bd.airwindow.ui.KindTag
import bd.airwindow.ui.OneUiScreen
import bd.airwindow.ui.ReplayBanner
import bd.airwindow.ui.SectionLabel
import bd.airwindow.ui.Segmented
import bd.airwindow.ui.Strings
import bd.airwindow.ui.theme.LocalAw

private val ACTS = listOf("walk", "exercise", "commute", "school_run", "errands")

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun PlanScreen(vm: AppViewModel, p: UserPrefs, s: Strings) {
    val c = LocalAw.current
    var act by rememberSaveable { mutableStateOf("walk") }
    LaunchedEffect(p.stationId, p.pollutant, act) { vm.refreshPlan(p, act) }
    val win by vm.planWindows.collectAsState()
    val meta by vm.meta.collectAsState()

    OneUiScreen(s.planTitle, sub = { Text(s.tagline, color = c.ink2, fontSize = 15.sp) }) {
        if (meta?.mode == "replay") item { ReplayBanner(s) }
        item {
            AwCard {
                Text(s.activity, fontSize = 13.sp, color = c.ink3, fontWeight = FontWeight.Medium)
                Spacer(Modifier.height(10.dp))
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    ACTS.forEach { a -> Chip(s.act(a), a == act) { act = a } }
                }
                Spacer(Modifier.height(18.dp))
                Text(s.pollutant, fontSize = 13.sp, color = c.ink3, fontWeight = FontWeight.Medium)
                Spacer(Modifier.height(10.dp))
                Segmented(p.pollutant, listOf("pm25" to "PM2.5", "pm10" to "PM10")) { v -> vm.update { it.copy(pollutant = v) } }
            }
        }
        item { SectionLabel(s.ranked) }
        when (val w = win) {
            is Load.Ok -> {
                item {
                    AwCard {
                        val list = w.value.windows
                        list.forEachIndexed { i, h ->
                            if (i > 0) HorizontalDivider(color = c.line)
                            Row(Modifier.padding(vertical = 14.dp), verticalAlignment = Alignment.CenterVertically) {
                                Box(Modifier.size(36.dp).clip(CircleShape).background(if (h.rank == 1) c.accentFill else c.card2),
                                    contentAlignment = Alignment.Center) {
                                    Text(s.n(h.rank), fontWeight = FontWeight.SemiBold, color = if (h.rank == 1) Color.White else c.ink)
                                }
                                Spacer(Modifier.width(14.dp))
                                Column(Modifier.weight(1f)) {
                                    Row(verticalAlignment = Alignment.Bottom) {
                                        Text(if (h.horizonH == 0) s.now else s.clock(h.validAt), fontWeight = FontWeight.SemiBold, fontSize = 17.sp)
                                        if (h.horizonH > 0) { Spacer(Modifier.width(8.dp)); Text(s.inHours(h.horizonH), fontSize = 13.sp, color = c.ink2) }
                                    }
                                    KindTag(h.kind == "measured", if (h.kind == "measured") s.measured else s.forecast)
                                    if (h.rank == 1 && list.size > 1)
                                        Text(if (h.clearlyLowerThanNext) s.clearlyLower else s.overlap, fontSize = 12.sp, color = c.ink3)
                                }
                                Column(horizontalAlignment = Alignment.End) {
                                    Text(s.n(h.value), fontWeight = FontWeight.SemiBold, fontSize = 20.sp)
                                    Text(if (h.lo80 != null && h.hi80 != null) "${s.n(h.lo80)}–${s.n(h.hi80)}" else "µg/m³", fontSize = 12.sp, color = c.ink3)
                                }
                            }
                        }
                    }
                }
                item { Text("${s.notSafety} · model ${w.value.modelVersion}", fontSize = 12.sp, color = c.ink3, modifier = Modifier.padding(horizontal = 8.dp)) }
            }
            is Load.Err -> item { AwCard(tone = "warn") { Text(w.message ?: s.errorGeneric) } }
            Load.Loading -> item { AwCard { Box(Modifier.height(220.dp)) } }
        }
    }
}

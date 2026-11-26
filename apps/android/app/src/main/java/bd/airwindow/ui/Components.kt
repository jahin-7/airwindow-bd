package bd.airwindow.ui

import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyListScope
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.runtime.derivedStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalDensity
import bd.airwindow.data.HourWindow
import bd.airwindow.ui.theme.LocalAw

val CardShape = RoundedCornerShape(26.dp)

/**
 * One UI-style screen: the big title sits in the top third as the first item of the list, so it
 * scrolls away with the content instead of resizing. A compact bar with the small title fades in
 * once it's gone. Nothing changes height while scrolling, so nothing below can jump.
 */
@Composable
fun OneUiScreen(title: String, sub: (@Composable () -> Unit)? = null, titleLines: Int = 1, content: LazyListScope.() -> Unit) {
    val c = LocalAw.current
    val list = rememberLazyListState()
    val density = LocalDensity.current
    // 0 while the big title is fully visible, 1 once it has scrolled out of view.
    val gone by remember {
        derivedStateOf {
            if (list.firstVisibleItemIndex > 0) 1f
            else with(density) { (list.firstVisibleItemScrollOffset / 140.dp.toPx()).coerceIn(0f, 1f) }
        }
    }
    val headerH = (LocalConfiguration.current.screenHeightDp * 0.3f).dp
    Box(Modifier.fillMaxSize().background(c.bg)) {
        LazyColumn(Modifier.fillMaxSize(), state = list,
            contentPadding = PaddingValues(start = 16.dp, end = 16.dp, bottom = 24.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)) {
            item(key = "header") {
                Column(
                    Modifier.fillMaxWidth().statusBarsPadding().heightIn(min = headerH).padding(start = 8.dp, end = 8.dp, bottom = 12.dp)
                        .graphicsLayer { alpha = 1f - gone; translationY = gone * 24.dp.toPx() },
                    verticalArrangement = Arrangement.Bottom,
                ) {
                    // [titleLines] reserves room for a title that changes with the data, so it can't push the page down.
                    Text(title, style = MaterialTheme.typography.displaySmall, color = c.ink, minLines = titleLines, maxLines = 3,
                        overflow = TextOverflow.Ellipsis)
                    if (sub != null) { Spacer(Modifier.height(10.dp)); sub() }
                }
            }
            content()
        }
        Box(
            Modifier.fillMaxWidth().graphicsLayer { alpha = ((gone - 0.6f) / 0.4f).coerceIn(0f, 1f) }
                .background(c.bg).statusBarsPadding().height(56.dp).padding(horizontal = 24.dp),
            contentAlignment = Alignment.CenterStart,
        ) {
            Text(title, style = MaterialTheme.typography.titleMedium, color = c.ink, maxLines = 1, overflow = TextOverflow.Ellipsis)
        }
    }
}

@Composable
fun AwCard(modifier: Modifier = Modifier, tone: String = "default", onClick: (() -> Unit)? = null, content: @Composable ColumnScope.() -> Unit) {
    val c = LocalAw.current
    val bg = when (tone) { "warn" -> c.warnSoft; "accent" -> c.accentSoft; else -> c.card }
    Column(
        modifier.fillMaxWidth().clip(CardShape).background(bg)
            .then(if (onClick != null) Modifier.clickable(onClick = onClick) else Modifier).padding(20.dp),
        content = content,
    )
}

@Composable
fun SectionLabel(text: String) {
    Text(text, Modifier.padding(start = 8.dp, top = 12.dp), style = MaterialTheme.typography.labelMedium, color = LocalAw.current.ink3)
}

/** Measured = solid dot; forecast = dashed ring in accent. Never colour alone. */
@Composable
fun KindTag(measured: Boolean, label: String) {
    val c = LocalAw.current
    Row(verticalAlignment = Alignment.CenterVertically) {
        if (measured) Box(Modifier.size(8.dp).clip(CircleShape).background(c.ink))
        else androidx.compose.foundation.Canvas(Modifier.size(9.dp)) {
            drawCircle(c.accent, style = Stroke(width = 2.dp.toPx(), pathEffect = PathEffect.dashPathEffect(floatArrayOf(3f, 3f))))
        }
        Spacer(Modifier.width(6.dp))
        Text(label, style = MaterialTheme.typography.labelSmall, color = if (measured) c.ink2 else c.accent, fontWeight = FontWeight.Medium)
    }
}

@Composable
fun <T> Segmented(value: T, options: List<Pair<T, String>>, onChange: (T) -> Unit) {
    val c = LocalAw.current
    Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(50)).background(c.card2).padding(4.dp)) {
        options.forEach { (v, label) ->
            val on = v == value
            Box(
                Modifier.weight(1f).clip(RoundedCornerShape(50)).background(if (on) c.card else Color.Transparent)
                    .clickable { onChange(v) }.padding(vertical = 10.dp),
                contentAlignment = Alignment.Center,
            ) { Text(label, fontSize = 14.sp, fontWeight = FontWeight.Medium, color = if (on) c.ink else c.ink2) }
        }
    }
}

@Composable
fun Chip(label: String, on: Boolean, onClick: () -> Unit) {
    val c = LocalAw.current
    Box(Modifier.clip(RoundedCornerShape(50)).background(if (on) c.accentFill else c.card2).clickable(onClick = onClick)
        .padding(horizontal = 16.dp, vertical = 9.dp)) {
        Text(label, fontSize = 14.sp, fontWeight = FontWeight.Medium, color = if (on) Color.White else c.ink)
    }
}

@Composable
fun ReplayBanner(s: Strings) {
    AwCard(tone = "warn") {
        Text(s.replayTitle, fontWeight = FontWeight.SemiBold, color = LocalAw.current.warn, fontSize = 13.sp)
        Text(s.replaySub, fontSize = 13.sp, color = LocalAw.current.ink2)
    }
}

/** Now + forecast hours as bars on one scale; forecast bars carry their 80% range. */
@Composable
fun HoursStrip(windows: List<HourWindow>, s: Strings) {
    val c = LocalAw.current
    val pts = windows.sortedBy { it.horizonH }
    val max = (pts.maxOfOrNull { it.hi80 ?: it.value } ?: 1.0) * 1.1
    Row(Modifier.fillMaxWidth().height(200.dp), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.Bottom) {
        pts.forEachIndexed { i, p ->
            val best = p.rank == 1
            val target = (p.value / max).toFloat()
            val frac by animateFloatAsState(target, spring(dampingRatio = 0.8f, stiffness = Spring.StiffnessLow), label = "bar$i")
            Column(Modifier.weight(1f).fillMaxHeight().semantics {
                contentDescription = "${if (p.horizonH == 0) s.now else s.clock(p.validAt)} ${p.value} µg/m³ ${if (p.kind == "measured") s.measured else s.forecast}"
            }, horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Bottom) {
                // value label sits directly on top of its bar
                BoxWithConstraints(Modifier.weight(1f).fillMaxWidth()) {
                    val barH = maxHeight * frac.coerceIn(0.02f, 0.85f)
                    Column(Modifier.fillMaxSize(), horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Bottom) {
                        Text(s.n(p.value), fontSize = 13.sp, fontWeight = FontWeight.SemiBold, color = if (best) c.accent else c.ink)
                        Spacer(Modifier.height(6.dp))
                        Box(Modifier.fillMaxWidth().height(barH).clip(RoundedCornerShape(14.dp)).then(
                            when {
                                p.kind == "measured" -> Modifier.background(c.ink)
                                best -> Modifier.background(c.accent)
                                else -> Modifier.border(BorderStroke(2.dp, c.accent), RoundedCornerShape(14.dp))
                            }))
                    }
                }
                Spacer(Modifier.height(8.dp))
                Text(if (p.horizonH == 0) s.now else s.clock(p.validAt), fontSize = 12.sp, color = c.ink2, textAlign = TextAlign.Center)
                if (p.lo80 != null && p.hi80 != null)
                    Text("${s.n(p.lo80)}–${s.n(p.hi80)}", fontSize = 11.sp, color = c.ink3)
                else Text(" ", fontSize = 11.sp)
            }
        }
    }
}

/** Colours come from the API; a malformed one falls back to grey rather than crashing the screen. */
fun hexColor(hex: String): Color = runCatching { Color(android.graphics.Color.parseColor(hex)) }.getOrDefault(Color.Gray)

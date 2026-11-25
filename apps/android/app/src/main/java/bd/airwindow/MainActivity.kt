package bd.airwindow

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.systemBarsPadding
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CalendarMonth
import androidx.compose.material.icons.outlined.LocationOn
import androidx.compose.material.icons.outlined.MoreHoriz
import androidx.compose.material.icons.outlined.ShowChart
import androidx.compose.material.icons.outlined.WbSunny
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import bd.airwindow.data.UserPrefs
import bd.airwindow.ui.Strings
import bd.airwindow.ui.screens.MoreScreen
import bd.airwindow.ui.screens.PlanScreen
import bd.airwindow.ui.screens.StationsScreen
import bd.airwindow.ui.screens.TodayScreen
import bd.airwindow.ui.screens.TrendsScreen
import bd.airwindow.ui.theme.AirWindowTheme
import bd.airwindow.ui.theme.LocalAw

class MainActivity : ComponentActivity() {
    private val vm: AppViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            val prefs by vm.prefs.collectAsState()
            val p = prefs ?: return@setContent // wait for DataStore
            AirWindowTheme(p.theme) {
                if (p.lang == null) Onboarding { lang -> vm.update { it.copy(lang = lang) } }
                else App(vm, p, Strings(p.lang == "bn"))
            }
        }
    }
}

private data class Tab(val route: String, val label: (Strings) -> String, val icon: androidx.compose.ui.graphics.vector.ImageVector)

private val TABS = listOf(
    Tab("today", { it.today }, Icons.Outlined.WbSunny),
    Tab("plan", { it.plan }, Icons.Outlined.CalendarMonth),
    Tab("stations", { it.stations }, Icons.Outlined.LocationOn),
    Tab("trends", { it.trends }, Icons.Outlined.ShowChart),
    Tab("more", { it.more }, Icons.Outlined.MoreHoriz),
)

@Composable
private fun App(vm: AppViewModel, p: UserPrefs, s: Strings) {
    val c = LocalAw.current
    val nav = rememberNavController()
    val current by nav.currentBackStackEntryAsState()
    fun go(route: String) = nav.navigate(route) {
        popUpTo(nav.graph.findStartDestination().id) { saveState = true }
        launchSingleTop = true
        restoreState = true
    }
    Scaffold(
        containerColor = c.bg,
        bottomBar = {
            NavigationBar(containerColor = c.bg, tonalElevation = 0.dp) {
                TABS.forEach { t ->
                    val on = current?.destination?.route == t.route
                    NavigationBarItem(
                        selected = on, onClick = { go(t.route) },
                        icon = { Icon(t.icon, contentDescription = null) },
                        label = { Text(t.label(s), fontSize = 11.sp, fontWeight = FontWeight.Medium) },
                        colors = NavigationBarItemDefaults.colors(selectedIconColor = c.accent, indicatorColor = c.accentSoft,
                            unselectedIconColor = c.ink2, selectedTextColor = c.ink, unselectedTextColor = c.ink2),
                    )
                }
            }
        },
    ) { pad ->
        NavHost(nav, "today", Modifier.padding(bottom = pad.calculateBottomPadding())) {
            composable("today") { TodayScreen(vm, p, s, openStations = { go("stations") }, openPlan = { go("plan") }) }
            composable("plan") { PlanScreen(vm, p, s) }
            composable("stations") { StationsScreen(vm, p, s, picked = { go("today") }) }
            composable("trends") { TrendsScreen(vm, p, s) }
            composable("more") { MoreScreen(vm, p, s) }
        }
    }
}

@Composable
private fun Onboarding(choose: (String) -> Unit) {
    val c = LocalAw.current
    var pick by remember { mutableStateOf("bn") }
    val s = Strings(pick == "bn")
    Column(Modifier.fillMaxSize().background(c.bg).systemBarsPadding().padding(horizontal = 24.dp, vertical = 24.dp)) {
        Spacer(Modifier.height(96.dp))
        Text("AirWindow · এয়ারউইন্ডো", color = c.accent, fontWeight = FontWeight.Medium)
        Spacer(Modifier.height(12.dp))
        Text(s.chooseLang, fontSize = 34.sp, fontWeight = FontWeight.SemiBold, lineHeight = 40.sp, color = c.ink)
        Spacer(Modifier.height(8.dp))
        Text(s.chooseLangSub, color = c.ink2)
        Spacer(Modifier.weight(1f))
        listOf(Triple("bn", "বাংলা", "Bangla"), Triple("en", "English", "ইংরেজি")).forEach { (v, a, b) ->
            Row(Modifier.fillMaxWidth().padding(vertical = 6.dp).clip(RoundedCornerShape(22.dp)).background(c.card)
                .border(2.dp, if (pick == v) c.accent else Color.Transparent, RoundedCornerShape(22.dp))
                .clickable { pick = v }.padding(20.dp), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(a, fontSize = 18.sp, fontWeight = FontWeight.SemiBold, color = c.ink)
                    Text(b, fontSize = 13.sp, color = c.ink2)
                }
                Box(Modifier.size(24.dp).clip(CircleShape).then(
                    if (pick == v) Modifier.background(c.accent) else Modifier.border(2.dp, c.line, CircleShape)))
            }
        }
        Spacer(Modifier.height(16.dp))
        Box(Modifier.fillMaxWidth().clip(RoundedCornerShape(50)).background(c.accentFill).clickable { choose(pick) }.padding(vertical = 16.dp),
            contentAlignment = Alignment.Center) {
            Text(s.cont, color = Color.White, fontSize = 17.sp, fontWeight = FontWeight.SemiBold)
        }
    }
}

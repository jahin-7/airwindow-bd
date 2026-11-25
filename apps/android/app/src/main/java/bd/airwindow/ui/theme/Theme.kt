package bd.airwindow.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

/** Same tokens as the web app (apps/web/src/app/globals.css). */
@Immutable
data class AwColors(
    val bg: Color, val card: Color, val card2: Color, val ink: Color, val ink2: Color, val ink3: Color,
    val line: Color, val accent: Color, val accentFill: Color, val accentSoft: Color, val warn: Color, val warnSoft: Color,
)

val LightAw = AwColors(
    bg = Color(0xFFF4F4F6), card = Color.White, card2 = Color(0xFFECECF0), ink = Color(0xFF0F0F12),
    ink2 = Color(0xFF5B5B66), ink3 = Color(0xFF8C8C96), line = Color(0xFFE2E2E8), accent = Color(0xFF3B7BFF),
    accentFill = Color(0xFF2563EB), accentSoft = Color(0xFFE3ECFF), warn = Color(0xFFB25B00), warnSoft = Color(0xFFFFF1E0),
)
val DarkAw = AwColors(
    bg = Color.Black, card = Color(0xFF17171A), card2 = Color(0xFF232327), ink = Color(0xFFF4F4F6),
    ink2 = Color(0xFFB4B4BD), ink3 = Color(0xFF82828C), line = Color(0xFF2C2C31), accent = Color(0xFF5C93FF),
    accentFill = Color(0xFF2563EB), accentSoft = Color(0xFF1B2A4A), warn = Color(0xFFFFB35C), warnSoft = Color(0xFF3A2810),
)

val LocalAw = staticCompositionLocalOf { LightAw }

@Composable
fun AirWindowTheme(theme: String, content: @Composable () -> Unit) {
    val dark = when (theme) { "dark" -> true; "light" -> false; else -> isSystemInDarkTheme() }
    val c = if (dark) DarkAw else LightAw
    val scheme = (if (dark) darkColorScheme() else lightColorScheme()).copy(
        primary = c.accentFill, onPrimary = Color.White, background = c.bg, onBackground = c.ink,
        surface = c.bg, onSurface = c.ink, surfaceVariant = c.card2, onSurfaceVariant = c.ink2,
        secondaryContainer = c.accentSoft, onSecondaryContainer = c.ink, outline = c.line,
    )
    val type = Typography(
        displaySmall = TextStyle(fontSize = 34.sp, fontWeight = FontWeight.SemiBold, lineHeight = 40.sp),
        headlineLarge = TextStyle(fontSize = 64.sp, fontWeight = FontWeight.SemiBold, lineHeight = 64.sp),
        titleLarge = TextStyle(fontSize = 20.sp, fontWeight = FontWeight.SemiBold),
        titleMedium = TextStyle(fontSize = 17.sp, fontWeight = FontWeight.SemiBold),
        bodyLarge = TextStyle(fontSize = 16.sp), bodyMedium = TextStyle(fontSize = 14.sp),
        labelMedium = TextStyle(fontSize = 13.sp, fontWeight = FontWeight.Medium),
        labelSmall = TextStyle(fontSize = 12.sp),
    )
    androidx.compose.runtime.CompositionLocalProvider(LocalAw provides c) {
        MaterialTheme(colorScheme = scheme, typography = type, content = content)
    }
}

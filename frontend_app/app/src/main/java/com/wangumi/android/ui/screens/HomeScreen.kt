package com.wangumi.android.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ChatBubble
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Movie
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.AssistChip
import androidx.compose.material3.AssistChipDefaults
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.FloatingActionButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shadow
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.util.lerp
import coil.compose.AsyncImage
import com.wangumi.android.MainViewModel
import com.wangumi.android.R
import com.wangumi.android.data.model.AnimeDetailResult
import com.wangumi.android.data.model.AnimeListResult
import com.wangumi.android.data.model.AnimeSummary
import com.wangumi.android.data.model.RecommendationItem
import com.wangumi.android.data.model.RecommendationResult
import com.wangumi.android.data.remote.NetworkResult
import java.time.LocalDate
import java.time.format.DateTimeParseException
import java.time.temporal.ChronoUnit
import kotlin.math.abs
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Outline
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.LayoutDirection
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.foundation.layout.calculateStartPadding
import androidx.compose.foundation.layout.calculateEndPadding
private val BottomBarBaseHeight = 116.dp
private val BottomBarBumpHeight = 24.dp
private val BackgroundColor = Color(0xFFF7F8FC)
private val PrimaryColor = Color(0xFF7B8CFF)
private val AccentColor = Color(0xFFFF82C8)
private val CardBackgroundColor = Color.White
private val TitleColor = Color(0xFF1A1A1A)
private val SecondaryTextColor = Color(0xFF6F6F6F)

@Composable
fun HomeScreen(
    onLogin: (String, String, (NetworkResult<Unit>) -> Unit) -> Unit,
    animeState: NetworkResult<AnimeListResult>,
    filters: MainViewModel.AnimeFilters,
    onSortChange: (String) -> Unit,
    onCategoryInput: (String) -> Unit,
    onApplyCategory: () -> Unit,
    onNextPage: () -> Unit,
    onPrevPage: () -> Unit,
    currentScreen: MainViewModel.Screen,
    editorState: NetworkResult<RecommendationResult>,
    hotState: NetworkResult<RecommendationResult>,
    onShowList: () -> Unit,
    onShowRecommend: () -> Unit,
    onShowSocial: () -> Unit,
    onShowHome: () -> Unit,
    onShowCreate: () -> Unit,
    onAnimeClick: (Int) -> Unit,
    detailState: NetworkResult<AnimeDetailResult>?,
    createForm: MainViewModel.CreateAnimeForm,
    onUpdateCreateForm: ((MainViewModel.CreateAnimeForm) -> MainViewModel.CreateAnimeForm) -> Unit,
    onSubmitCreate: () -> Unit,
    createState: NetworkResult<Unit>?,
    canCreate: Boolean
) {
    var username by rememberSaveable { mutableStateOf("") }
    var password by rememberSaveable { mutableStateOf("") }
    var loginMessage by remember { mutableStateOf("") }
    var loggingIn by remember { mutableStateOf(false) }

    Scaffold(
        containerColor = BackgroundColor,
        bottomBar = {
            BottomNavigationBar(
                currentScreen = currentScreen,
                canCreate = canCreate,
                onShowList = onShowList,
                onShowRecommend = onShowRecommend,
                onShowSocial = onShowSocial,
                onShowHome = onShowHome,
                onShowCreate = onShowCreate
            )
        }
    ) { innerPadding ->

        val layoutDir = LocalLayoutDirection.current
        val contentBottomPadding = innerPadding.calculateBottomPadding()

        LazyColumn(
            modifier = Modifier
                .padding(
                    start = innerPadding.calculateStartPadding(layoutDir),
                    top = innerPadding.calculateTopPadding(),
                    end = innerPadding.calculateEndPadding(layoutDir),
                    bottom = contentBottomPadding
                )
                .padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
            contentPadding = PaddingValues(bottom = 0.dp)
        )  {
            item {
                HeroSection(
                    onShowList = onShowList,
                    canCreate = canCreate,
                    onCreate = onShowCreate,
                    currentScreen = currentScreen
                )
            }
            when (currentScreen) {
                MainViewModel.Screen.List -> {
                    item {
                        AnimeFilterBlock(
                            state = animeState,
                            filters = filters,
                            onSortChange = onSortChange,
                            onCategoryInput = onCategoryInput,
                            onApplyCategory = onApplyCategory
                        )
                    }
                    when (animeState) {
                        is NetworkResult.Loading -> item { CenterLoading() }
                        is NetworkResult.Error -> item { ErrorText(animeState.message) }
                        is NetworkResult.Success -> {
                            items(animeState.data.list) { anime ->
                                AnimeCard(anime = anime, onAnimeClick = onAnimeClick)
                            }
                            item {
                                PaginationBlock(
                                    paginationLabel = "第 ${animeState.data.pagination.page} / ${animeState.data.pagination.pages} 页",
                                    onPrevPage = onPrevPage,
                                    onNextPage = onNextPage,
                                    canGoPrev = animeState.data.pagination.page > 1,
                                    canGoNext = animeState.data.pagination.page < animeState.data.pagination.pages
                                )
                            }
                        }
                    }
                }
                MainViewModel.Screen.Recommend -> {
                    item {
                        RecommendationScreen(
                            editorState = editorState,
                            hotState = hotState
                        )
                    }
                }
                MainViewModel.Screen.Social -> {
                    item { SocialSection() }
                }
                MainViewModel.Screen.Home -> {
                    item { HomeSection() }
                }
                is MainViewModel.Screen.Detail -> {
                    item {
                        DetailSection(
                            animeId = currentScreen.animeId,
                            state = detailState,
                            onBack = onShowList
                        )
                    }
                }
                MainViewModel.Screen.Create -> {
                    item {
                        CreateAnimeSection(
                            form = createForm,
                            onUpdate = onUpdateCreateForm,
                            onSubmit = onSubmitCreate,
                            createState = createState,
                            canCreate = canCreate
                        )
                    }
                }
            }
            item {
                LoginSection(
                    username = username,
                    password = password,
                    loggingIn = loggingIn,
                    loginMessage = loginMessage,
                    onUsernameChange = { username = it },
                    onPasswordChange = { password = it },
                    onLogin = {
                        loggingIn = true
                        loginMessage = ""
                        onLogin(username, password) { result ->
                            loggingIn = false
                            loginMessage = when (result) {
                                is NetworkResult.Success -> "登录成功"
                                is NetworkResult.Error -> result.message
                                NetworkResult.Loading -> "正在登录……"
                            }
                        }
                    }
                )
            }
        }
    }
}
@Composable
private fun HeroSection(
    onShowList: () -> Unit,
    canCreate: Boolean,
    onCreate: () -> Unit,
    currentScreen: MainViewModel.Screen
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color.Transparent),
        elevation = CardDefaults.cardElevation(defaultElevation = 6.dp)
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(200.dp)
                .clip(RoundedCornerShape(16.dp))
        ) {
            // 1. 背景图片铺满
            Image(
                painter = painterResource(id = R.drawable.frontpg),
                contentDescription = "Hero Background",
                modifier = Modifier.fillMaxSize(),
                contentScale = ContentScale.Crop
            )

            // 2. 渐变蒙版（可选，让文字更清晰）
            Box(
                modifier = Modifier
                    .matchParentSize()
                    .background(
                        Brush.horizontalGradient(
                            colors = listOf(
                                Color(0xCCFFFFFF),     // 左侧偏亮
                                Color(0x66FFFFFF)      // 右侧更透明
                            )
                        )
                    )
            )

            // 3. 文本 + 按钮内容
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(20.dp),
                verticalArrangement = Arrangement.Center
            ) {
                Text(
                    text = "Wangumi",
                    style = MaterialTheme.typography.displaySmall.copy(
                        fontWeight = FontWeight.Black,
                        color = Color(0xFF7469FF)
                    )
                )
                Text(
                    text = "发现喜欢的番剧",
                    style = MaterialTheme.typography.titleMedium.copy(
                        color = Color(0xFF4C88FF),
                        shadow = Shadow(
                            color = Color(0x884C88FF),
                            offset = Offset(0f, 4f),
                            blurRadius = 12f
                        )
                    )
                )
                Text(
                    text = "精选热播、治愈日常、奇幻冒险，一键进入二次元世界。",
                    style = MaterialTheme.typography.bodyMedium.copy(
                        color = Color(0xFF444444)
                    )
                )
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Button(
                        onClick = onShowList,
                        shape = RoundedCornerShape(24.dp),
                        modifier = Modifier.padding(top = 12.dp)
                    ) {
                        Text("立即探索")
                    }
                }
            }
        }
    }
}

// 顶部有中间凸起的小弧线
class BezierBottomBarShape(
    private val curveWidth: Dp = 96.dp,   // 中间拱形宽度
    private val curveHeight: Dp = 24.dp   // 拱形高度（越大越明显）
) : Shape {

    override fun createOutline(
        size: Size,
        layoutDirection: LayoutDirection,
        density: Density
    ): Outline {
        val w = size.width
        val h = size.height

        val curveWidthPx = with(density) { curveWidth.toPx() }
        val curveHeightPx = with(density) { curveHeight.toPx() }

        val centerX = w / 2f
        val halfCurve = curveWidthPx / 2f

        val path = Path().apply {
            // y 轴向下，所以 0 是最高点
            val flatY = curveHeightPx        // 左右两侧的“直线”高度

            // 左上
            moveTo(0f, flatY)
            // 到拱形左端
            lineTo(centerX - halfCurve, flatY)

            // 中间向上抬（最高点在 y=0）
            quadraticBezierTo(
                centerX, 0f,                       // 控制点：最高
                centerX + halfCurve, flatY        // 回到直线
            )

            // 右上
            lineTo(w, flatY)
            // 右下
            lineTo(w, h)
            // 左下
            lineTo(0f, h)
            close()
        }
        return Outline.Generic(path)
    }
}

@Composable
fun BottomNavigationBar(
    currentScreen: MainViewModel.Screen,
    canCreate: Boolean,
    onShowList: () -> Unit,
    onShowRecommend: () -> Unit,
    onShowSocial: () -> Unit,
    onShowHome: () -> Unit,
    onShowCreate: () -> Unit
) {
    val selectedTab: MainViewModel.Screen? = when (currentScreen) {
        is MainViewModel.Screen.Detail -> MainViewModel.Screen.List
        MainViewModel.Screen.Create -> null
        else -> currentScreen
    }

    val barHeight = BottomBarBaseHeight      // 真正放图标的高度
    val bumpHeight = BottomBarBumpHeight     // 上面凸起高度
    val shape = BezierBottomBarShape(
        curveWidth = 80.dp,    // 再窄一点
        curveHeight = bumpHeight
    )

    Box(
        modifier = Modifier
            .fillMaxWidth()
            // 外层高度等于真正“直线”部分，方便内容向下延伸
            .height(barHeight)
            .background(Color.Transparent)
    ) {
        // 用 Box 自己 clip + background，确保按 shape 画
        Box(
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .offset(y = -bumpHeight)              // 让凸起悬浮到内容之上
                .fillMaxWidth()
                .height(barHeight + bumpHeight)
                .clip(shape)
                .background( Color(0xFFE6F3FF))      // 底栏颜色，建议和 Scaffold 不同一点
        ) {
            // 导航内容贴在底部
            Row(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .fillMaxWidth()
                    .height(barHeight)
                    .padding(horizontal = 16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // 左两个
                BottomNavItem(
                    icon = Icons.Filled.Movie,
                    label = "番剧",
                    selected = selectedTab == MainViewModel.Screen.List,
                    onClick = onShowList,
                    modifier = Modifier.weight(1f)
                )
                BottomNavItem(
                    icon = Icons.Filled.Star,
                    label = "推荐",
                    selected = selectedTab == MainViewModel.Screen.Recommend,
                    onClick = onShowRecommend,
                    modifier = Modifier.weight(1f)
                )

                // 中间 +
                CenterCreateItem(
                    canCreate = canCreate,
                    isActive = currentScreen is MainViewModel.Screen.Create,
                    onShowCreate = onShowCreate,
                    modifier = Modifier.weight(1f)
                )

                // 右两个
                BottomNavItem(
                    icon = Icons.Filled.ChatBubble,
                    label = "社交",
                    selected = selectedTab == MainViewModel.Screen.Social,
                    onClick = onShowSocial,
                    modifier = Modifier.weight(1f)
                )
                BottomNavItem(
                    icon = Icons.Filled.Home,
                    label = "主页",
                    selected = selectedTab == MainViewModel.Screen.Home,
                    onClick = onShowHome,
                    modifier = Modifier.weight(1f)
                )
            }
        }
    }
}
@Composable
private fun BottomNavItem(
    icon: ImageVector,
    label: String,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val selectedColor = Color(0xFF2B6FF8)
    val unselectedColor = Color(0xFF9AA8C0)

    Column(
        modifier = modifier
            .clip(RoundedCornerShape(16.dp))
            .clickable(onClick = onClick)
            .padding(horizontal = 4.dp, vertical = 4.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        Box(
            modifier = Modifier
                .size(40.dp)
                .background(
                    color = if (selected) Color(0xFFE3EEFF) else Color.Transparent,
                    shape = RoundedCornerShape(14.dp)
                ),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = label,
                tint = if (selected) selectedColor else unselectedColor
            )
        }
        Text(
            text = label,
            color = if (selected) selectedColor else unselectedColor,
            style = MaterialTheme.typography.labelMedium
        )
    }
}

@Composable
private fun CenterCreateItem(
    canCreate: Boolean,
    isActive: Boolean,
    onShowCreate: () -> Unit,
    modifier: Modifier = Modifier
) {
    val bgColor = when {
        isActive -> Color(0xFF79C6FF)
        canCreate -> Color(0xFFCDEBFF)
        else -> Color(0xFFE5EFF8)
    }

    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Box(
            modifier = Modifier
                .size(48.dp)
                .offset(y = (-8).dp)   // 略微钻进上面的凸起
                .background(bgColor, CircleShape)
                .clickable(enabled = canCreate) {
                    if (canCreate) onShowCreate()
                },
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = Icons.Filled.Add,
                contentDescription = "创建番剧条目",
                tint = Color(0xFF0B4E86)
            )
        }

        Text(
            text = if (canCreate) "创建条目" else "登录后创建",
            color = Color(0xFF0B4E86),
            style = MaterialTheme.typography.labelSmall
        )
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun AnimeFilterBlock(
    state: NetworkResult<AnimeListResult>,
    filters: MainViewModel.AnimeFilters,
    onSortChange: (String) -> Unit,
    onCategoryInput: (String) -> Unit,
    onApplyCategory: () -> Unit
) {
    val sortOptions = listOf("热度", "时间", "评分")
    val categoryOptions = listOf("Action", "Fantasy", "Adventure", "Drama", "Comedy", "Romance")
    val selectedCategories = filters.categoryInput.split(",").map { it.trim() }.filter { it.isNotBlank() }.toMutableSet()
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text("排序方式", style = MaterialTheme.typography.titleMedium)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                sortOptions.forEach { option ->
                    FilterChip(
                        selected = filters.sort == option,
                        onClick = { onSortChange(option) },
                        label = { Text(option) },
                        colors = FilterChipDefaults.filterChipColors(
                            containerColor = Color(0xFFE6EAFF),
                            selectedContainerColor = Color(0xFFC8D1FF)
                        )
                    )
                }
            }
            Text("分类筛选", style = MaterialTheme.typography.titleMedium)
            FlowRow(
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                categoryOptions.forEach { category ->
                    val selected = selectedCategories.contains(category)
                    AssistChip(
                        onClick = {
                            if (selected) selectedCategories.remove(category) else selectedCategories.add(category)
                            onCategoryInput(selectedCategories.joinToString(","))
                            onApplyCategory()
                        },
                        label = { Text(category) },
                        shape = RoundedCornerShape(50),
                        colors = AssistChipDefaults.assistChipColors(
                            containerColor = if (selected) Color(0xFFDDE8FF) else MaterialTheme.colorScheme.surfaceVariant
                        )
                    )
                }
            }
            if (state is NetworkResult.Success) {
                Text(
                    text = "共 ${state.data.pagination.total} 部番剧",
                    style = MaterialTheme.typography.bodySmall
                )
            }
        }
    }
}

@Composable
private fun AnimeCard(anime: AnimeSummary, onAnimeClick: (Int) -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onAnimeClick(anime.id) },
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        elevation = CardDefaults.cardElevation(defaultElevation = 6.dp)
    ) {
        Column {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(6.dp)
                    .background(
                        brush = Brush.horizontalGradient(
                            listOf(Color(0xFFAEC8FF), Color(0xFFB4E1FF))
                        )
                    )
            )
            Row(
                modifier = Modifier.padding(16.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                AsyncImage(
                    model = anime.cover,
                    contentDescription = anime.title,
                    modifier = Modifier
                        .weight(0.35f)
                        .height(140.dp)
                        .clip(RoundedCornerShape(12.dp)),
                    contentScale = ContentScale.Crop
                )
                Column(
                    modifier = Modifier.weight(0.65f),
                    verticalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Text(
                        text = anime.title ?: "未命名番剧",
                        style = MaterialTheme.typography.titleMedium.copy(fontWeight = FontWeight.Bold),
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                    val categoryText = anime.category?.takeIf { it.isNotEmpty() }?.joinToString(" / ")
                    if (!categoryText.isNullOrBlank()) {
                        Text(text = categoryText, style = MaterialTheme.typography.bodySmall)
                    }
                    Text(text = anime.summary ?: "暂无简介", maxLines = 3, overflow = TextOverflow.Ellipsis)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        AssistChip(
                            onClick = {},
                            label = { Text(text = "⭐ ${anime.rating ?: "--"}") },
                            colors = AssistChipDefaults.assistChipColors(
                                containerColor = Color(0xFFE4E8FF),
                                labelColor = Color(0xFF2F3E9D)
                            )
                        )
                        AssistChip(
                            onClick = {},
                            label = { Text(text = "🔥 ${anime.popularity ?: "--"}") },
                            colors = AssistChipDefaults.assistChipColors(
                                containerColor = Color(0xFFDDF3FF),
                                labelColor = Color(0xFF0D5E9E)
                            )
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun PaginationBlock(
    paginationLabel: String,
    onPrevPage: () -> Unit,
    onNextPage: () -> Unit,
    canGoPrev: Boolean,
    canGoNext: Boolean
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Button(onClick = onPrevPage, enabled = canGoPrev) { Text("上一页") }
        Text(paginationLabel)
        Button(onClick = onNextPage, enabled = canGoNext) { Text("下一页") }
    }
}

@Composable
private fun DetailSection(
    animeId: Int,
    state: NetworkResult<AnimeDetailResult>?,
    onBack: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(text = "番剧详情 #$animeId", style = MaterialTheme.typography.titleMedium)
            when (state) {
                null -> Text("正在加载详情…")
                is NetworkResult.Loading -> CenterLoading()
                is NetworkResult.Error -> ErrorText(state.message)
                is NetworkResult.Success -> {
                    val basic = state.data.data.basic
                    if (basic != null) {
                        AsyncImage(
                            model = basic.cover,
                            contentDescription = basic.title,
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(280.dp)
                                .clip(RoundedCornerShape(16.dp)),
                            contentScale = ContentScale.Crop
                        )
                        Text(basic.title ?: "", style = MaterialTheme.typography.titleLarge)
                        Text(basic.summary ?: "暂无简介")
                    }
                    val meta = state.data.data.meta
                    if (meta != null) {
                        Text("状态：${meta.status ?: "未知"}")
                        Text("更新：${meta.updateProgress ?: "-"}")
                        Text("分类：${meta.category?.joinToString() ?: "无"}")
                    }
                    val comments = state.data.data.comments?.list.orEmpty()
                    if (comments.isNotEmpty()) {
                        Text("最新评论", fontWeight = FontWeight.Bold)
                        comments.take(5).forEach {
                            Text("${it.user ?: "匿名"}：${it.content}")
                        }
                    }
                }
            }
            Button(onClick = onBack) { Text("返回列表") }
        }
    }
}

@Composable
private fun RecommendationScreen(
    editorState: NetworkResult<RecommendationResult>,
    hotState: NetworkResult<RecommendationResult>
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(28.dp)
    ) {
        SectionHeader(title = "编辑精选", subtitle = "Editor's Pick")
        RecommendationStateBlock(editorState) { EditorsPickSection(it) }

        SectionHeader(title = "🔥 今日最火", subtitle = "热门 Top 榜")
        RecommendationStateBlock(hotState) { HotRankingSection(it) }

        SectionHeader(title = "🕒 本季新番，不容错过", subtitle = "新番速递")
        RecommendationStateBlock(editorState) { items ->
            val seasonalItems = items.filter { it.isRecentSeason() }.ifEmpty { items.take(6) }
            SeasonalHighlightsSection(seasonalItems)
        }
    }
}

@Composable
private fun SectionHeader(title: String, subtitle: String) {
    Column {
        Text(
            text = title,
            style = MaterialTheme.typography.titleMedium.copy(
                fontWeight = FontWeight.Bold,
                color = TitleColor
            )
        )
        Text(
            text = subtitle,
            style = MaterialTheme.typography.bodySmall.copy(color = SecondaryTextColor)
        )
    }
}

@Composable
private fun RecommendationStateBlock(
    state: NetworkResult<RecommendationResult>,
    content: @Composable (List<RecommendationItem>) -> Unit
) {
    when (state) {
        is NetworkResult.Loading -> CenterLoading()
        is NetworkResult.Error -> ErrorText(state.message)
        is NetworkResult.Success -> {
            if (state.data.list.isEmpty()) {
                Text("暂无推荐，稍后再试", color = SecondaryTextColor)
            } else {
                content(state.data.list)
            }
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun EditorsPickSection(items: List<RecommendationItem>) {
    val pagerState = rememberPagerState(pageCount = { items.size.coerceAtLeast(1) })
    HorizontalPager(
        state = pagerState,
        contentPadding = PaddingValues(horizontal = 56.dp),
        pageSpacing = 20.dp
    ) { page ->
        val item = items.getOrNull(page) ?: return@HorizontalPager
        val pageOffset = (pagerState.currentPage - page) + pagerState.currentPageOffsetFraction
        val normalizedOffset = abs(pageOffset).coerceIn(0f, 1f)
        val scale = lerp(0.85f, 1f, 1f - normalizedOffset)
        val alpha = lerp(0.3f, 1f, 1f - normalizedOffset)

        Card(
            modifier = Modifier
                .graphicsLayer {
                    scaleX = scale
                    scaleY = scale
                    this.alpha = alpha
                }
                .fillMaxWidth()
                .aspectRatio(9f / 16f),
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = CardBackgroundColor),
            elevation = CardDefaults.cardElevation(16.dp)
        ) {
            Box {
                AsyncImage(
                    model = item.cover,
                    contentDescription = item.title,
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.fillMaxSize()
                )
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(
                            Brush.verticalGradient(
                                listOf(Color.Transparent, Color(0xCC000000))
                            )
                        )
                )
                Column(
                    modifier = Modifier
                        .align(Alignment.BottomStart)
                        .padding(20.dp),
                    verticalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Text(
                        text = item.title ?: "未命名番剧",
                        style = MaterialTheme.typography.titleLarge.copy(
                            fontWeight = FontWeight.ExtraBold,
                            color = Color.White
                        ),
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                    Text(
                        text = item.summary?.takeIf { it.isNotBlank() } ?: "暂无简介",
                        style = MaterialTheme.typography.bodyMedium.copy(color = Color.White.copy(alpha = 0.85f)),
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis
                    )
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        RatingBadge(item.rating)
                        Text(
                            text = item.reason ?: "",
                            color = Color.White,
                            style = MaterialTheme.typography.labelMedium
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun HotRankingSection(items: List<RecommendationItem>) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = CardBackgroundColor),
        shape = RoundedCornerShape(20.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 10.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                text = "🔥 今日最热番剧",
                style = MaterialTheme.typography.titleMedium.copy(
                    fontWeight = FontWeight.Bold,
                    color = TitleColor
                )
            )
            LazyRow(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                items(items.size) { index ->
                    HotAnimeCard(item = items[index], rank = index + 1)
                }
            }
        }
    }
}

@Composable
private fun HotAnimeCard(item: RecommendationItem, rank: Int) {
    val badge = when (rank) {
        1 -> "🥇"
        2 -> "🥈"
        3 -> "🥉"
        else -> "TOP $rank"
    }
    Card(
        modifier = Modifier
            .width(160.dp),
        colors = CardDefaults.cardColors(containerColor = CardBackgroundColor),
        shape = RoundedCornerShape(16.dp),
        elevation = CardDefaults.cardElevation(8.dp)
    ) {
        Column(
            modifier = Modifier.padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .aspectRatio(9f / 13f)
                    .clip(RoundedCornerShape(12.dp))
            ) {
                AsyncImage(
                    model = item.cover,
                    contentDescription = item.title,
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.fillMaxSize()
                )
                Text(
                    text = badge,
                    modifier = Modifier
                        .align(Alignment.TopStart)
                        .padding(8.dp)
                        .background(Color.White.copy(alpha = 0.8f), RoundedCornerShape(12.dp))
                        .padding(horizontal = 8.dp, vertical = 4.dp),
                    style = MaterialTheme.typography.labelMedium.copy(color = TitleColor)
                )
            }
            Text(
                text = item.title ?: "未命名",
                style = MaterialTheme.typography.bodyMedium.copy(
                    fontWeight = FontWeight.Medium,
                    color = TitleColor
                ),
                maxLines = 2,
                overflow = TextOverflow.Ellipsis
            )
            RatingBadge(item.rating)
        }
    }
}

@Composable
private fun RatingBadge(rating: Double?) {
    if (rating == null) return
    Surface(
        color = AccentColor.copy(alpha = 0.15f),
        shape = RoundedCornerShape(32.dp)
    ) {
        Text(
            text = "评分 ${String.format("%.1f", rating)}",
            modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
            style = MaterialTheme.typography.labelMedium.copy(color = AccentColor)
        )
    }
}

@Composable
private fun SeasonalHighlightsSection(items: List<RecommendationItem>) {
    if (items.isEmpty()) {
        Text("暂无本季番剧", color = SecondaryTextColor)
        return
    }
    val rows = items.chunked(2)
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        rows.forEach { rowItems ->
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                rowItems.forEach { item ->
                    SeasonalAnimeCard(
                        modifier = Modifier.weight(1f),
                        item = item
                    )
                }
                if (rowItems.size == 1) {
                    Spacer(modifier = Modifier.weight(1f))
                }
            }
        }
    }
}

@Composable
private fun SeasonalAnimeCard(
    modifier: Modifier = Modifier,
    item: RecommendationItem
) {
    val total = item.totalEpisodes?.takeIf { it > 0 } ?: 12
    val released = (item.episodesReleased ?: (total / 2).coerceAtLeast(1)).coerceAtMost(total)
    val progress = released.toFloat() / total.toFloat()
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = CardBackgroundColor),
        elevation = CardDefaults.cardElevation(6.dp)
    ) {
        Column(
            modifier = Modifier.padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            AsyncImage(
                model = item.cover,
                contentDescription = item.title,
                modifier = Modifier
                    .fillMaxWidth()
                    .aspectRatio(3f / 4f)
                    .clip(RoundedCornerShape(16.dp)),
                contentScale = ContentScale.Crop
            )
            Text(
                text = item.title ?: "未命名番剧",
                style = MaterialTheme.typography.bodyMedium.copy(
                    fontWeight = FontWeight.SemiBold,
                    color = TitleColor
                ),
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
            LinearProgressIndicator(
                progress = { progress },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(8.dp)
                    .clip(RoundedCornerShape(32.dp)),
                color = PrimaryColor,
                trackColor = Color(0xFFE2E6F4)
            )
            Text(
                text = "更新至 $released / $total 集",
                style = MaterialTheme.typography.labelSmall.copy(color = SecondaryTextColor)
            )
        }
    }
}

@Composable
private fun SocialSection() {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("社交广场", style = MaterialTheme.typography.titleMedium)
            Text("看看大家在追什么番，发布你的讨论与短评。")
        }
    }
}

@Composable
private fun HomeSection() {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text("主页", style = MaterialTheme.typography.titleMedium)
            Text("收藏的番剧、订阅的推荐和应用动态都会在这里汇总展示。")
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                AssistChip(
                    onClick = {},
                    label = { Text("我的收藏") },
                    colors = AssistChipDefaults.assistChipColors(containerColor = Color(0xFFE4F1FF))
                )
                AssistChip(
                    onClick = {},
                    label = { Text("待看清单") },
                    colors = AssistChipDefaults.assistChipColors(containerColor = Color(0xFFEAF8FF))
                )
            }
        }
    }
}

@Composable
private fun CreateAnimeSection(
    form: MainViewModel.CreateAnimeForm,
    onUpdate: ((MainViewModel.CreateAnimeForm) -> MainViewModel.CreateAnimeForm) -> Unit,
    onSubmit: () -> Unit,
    createState: NetworkResult<Unit>?,
    canCreate: Boolean
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color.Transparent)
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("创建新条目", style = MaterialTheme.typography.titleMedium)
            Text("新建条目默认 is_admin = false，管理员审核通过后将标记为官方番剧。", style = MaterialTheme.typography.bodySmall)
            OutlinedTextField(
                value = form.title,
                onValueChange = { value -> onUpdate { it.copy(title = value) } },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("标题*") }
            )
            OutlinedTextField(
                value = form.titleJapanese,
                onValueChange = { value -> onUpdate { it.copy(titleJapanese = value) } },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("日文标题") }
            )
            OutlinedTextField(
                value = form.summary,
                onValueChange = { value -> onUpdate { it.copy(summary = value) } },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("简介") }
            )
            OutlinedTextField(
                value = form.categoryInput,
                onValueChange = { value -> onUpdate { it.copy(categoryInput = value) } },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("分类（逗号分隔）") }
            )
            OutlinedTextField(
                value = form.releaseDate,
                onValueChange = { value -> onUpdate { it.copy(releaseDate = value) } },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("首播日期 YYYY-MM-DD") }
            )
            OutlinedTextField(
                value = form.status,
                onValueChange = { value -> onUpdate { it.copy(status = value) } },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("状态") }
            )
            OutlinedTextField(
                value = form.totalEpisodes,
                onValueChange = { value -> onUpdate { it.copy(totalEpisodes = value) } },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("总集数") }
            )
            OutlinedTextField(
                value = form.coverUrl,
                onValueChange = { value -> onUpdate { it.copy(coverUrl = value) } },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("封面 URL") }
            )
            Button(onClick = onSubmit, enabled = form.title.isNotBlank() && canCreate) {
                Text(if (canCreate) "提交" else "请先登录")
            }
            when (createState) {
                is NetworkResult.Loading -> CenterLoading()
                is NetworkResult.Error -> ErrorText(createState.message)
                is NetworkResult.Success -> Text("创建成功！", color = MaterialTheme.colorScheme.primary)
                null -> {}
            }
        }
    }
}

@Composable
private fun CenterLoading() {
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center) {
        CircularProgressIndicator()
    }
}

@Composable
private fun ErrorText(message: String) {
    Text(text = message, color = MaterialTheme.colorScheme.error)
}

@Composable
private fun LoginSection(
    username: String,
    password: String,
    loggingIn: Boolean,
    loginMessage: String,
    onUsernameChange: (String) -> Unit,
    onPasswordChange: (String) -> Unit,
    onLogin: () -> Unit
) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Text(text = "登录", style = MaterialTheme.typography.titleMedium)
        OutlinedTextField(
            modifier = Modifier.fillMaxWidth(),
            value = username,
            onValueChange = onUsernameChange,
            label = { Text("用户名") }
        )
        OutlinedTextField(
            modifier = Modifier.fillMaxWidth(),
            value = password,
            onValueChange = onPasswordChange,
            label = { Text("密码") },
            visualTransformation = PasswordVisualTransformation()
        )
        Button(
            modifier = Modifier.fillMaxWidth(),
            enabled = username.isNotBlank() && password.isNotBlank() && !loggingIn,
            onClick = onLogin
        ) {
            Text(if (loggingIn) "登录中…" else "尝试登录")
        }
        if (loginMessage.isNotEmpty()) {
            Text(loginMessage, color = MaterialTheme.colorScheme.primary)
        }
    }
}

private fun RecommendationItem.isRecentSeason(): Boolean {
    val release = parseReleaseDate(releaseDate) ?: return false
    val days = ChronoUnit.DAYS.between(release, LocalDate.now())
    return days in 0..120
}

private fun parseReleaseDate(date: String?): LocalDate? = try {
    date?.takeIf { it.isNotBlank() }?.let { LocalDate.parse(it) }
} catch (_: DateTimeParseException) {
    null
}

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from collections import Counter
import jieba
from wordcloud import WordCloud
from matplotlib.ticker import PercentFormatter
from scipy.interpolate import make_interp_spline
import warnings
warnings.filterwarnings('ignore')

# 解决中文显示问题
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
matplotlib.rcParams['axes.unicode_minus'] = False

# 设置统一的颜色主题
COLOR_PALETTE = {
    'primary': '#3498db',      # 蓝色
    'secondary': '#2ecc71',    # 绿色
    'tertiary': '#e74c3c',     # 红色
    'quaternary': '#f39c12',   # 橙色
    'gray': '#95a5a6',         # 灰色
    'dark': '#2c3e50'          # 深色
}

# 创建图表保存目录
chart_dir = os.path.join('chart', 'images')
os.makedirs(chart_dir, exist_ok=True)

def create_style_plot(title, figsize=(12, 7)):
    """创建统一风格的图表"""
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_facecolor('#f8f9fa')
    fig.patch.set_facecolor('#ffffff')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#bdc3c7')
    ax.spines['bottom'].set_color('#bdc3c7')
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20, color=COLOR_PALETTE['dark'])
    ax.grid(True, alpha=0.3, linestyle='--')
    return fig, ax

# ============================================================================
# 1. 分析视频互动数据的基本构成
# ============================================================================

def analyze_video_engagement():
    """分析视频互动数据的基本构成"""
    print("\n" + "="*60)
    print("1. 视频互动数据分析")
    print("="*60)
    
    video_dir = os.path.join('data', 'video')
    video_csv_files = [f for f in os.listdir(video_dir) if f.endswith('_视频.csv')]
    
    if not video_csv_files:
        print(f"警告：{video_dir} 中未找到 *_视频.csv 文件")
        return
    
    for video_csv_file in video_csv_files:
        video_file_path = os.path.join(video_dir, video_csv_file)
        print(f"\n处理视频文件: {video_csv_file}")
        
        try:
            video_df = pd.read_csv(video_file_path)
            
            required_columns = ['精确播放数', '点赞数', '评论数', '收藏人数', '转发人数']
            missing_columns = [col for col in required_columns if col not in video_df.columns]
            
            if missing_columns:
                print(f"  警告：文件缺少必要列 {missing_columns}")
                continue
            
            for idx, row in video_df.iterrows():
                video_identifier = row.get('标题', f'视频_{idx+1}')
                if pd.isna(video_identifier) or video_identifier == '':
                    video_identifier = f'视频_{idx+1}'
                
                print(f"  分析视频: {video_identifier}")
                
                play_count = float(row['精确播放数']) if not pd.isna(row['精确播放数']) else 0
                like_count = float(row['点赞数']) if not pd.isna(row['点赞数']) else 0
                comment_count = float(row['评论数']) if not pd.isna(row['评论数']) else 0
                favorite_count = float(row['收藏人数']) if not pd.isna(row['收藏人数']) else 0
                share_count = float(row['转发人数']) if not pd.isna(row['转发人数']) else 0
                
                epsilon = 1e-10
                like_ratio = (like_count / (play_count + epsilon)) * 100
                comment_ratio = (comment_count / (play_count + epsilon)) * 100
                favorite_ratio = (favorite_count / (play_count + epsilon)) * 100
                share_ratio = (share_count / (play_count + epsilon)) * 100
                
                # 创建互动比例柱状图
                fig, ax = create_style_plot(f'{video_identifier}\n互动行为占播放量比例分析', figsize=(10, 6))
                
                categories = ['点赞比例', '评论比例', '收藏比例', '转发比例']
                ratios = [like_ratio, comment_ratio, favorite_ratio, share_ratio]
                colors = [COLOR_PALETTE['primary'], COLOR_PALETTE['secondary'], 
                         COLOR_PALETTE['tertiary'], COLOR_PALETTE['quaternary']]
                
                bars = ax.bar(categories, ratios, color=colors, edgecolor='white', linewidth=2)
                ax.set_ylabel('百分比 (%)', fontsize=12)
                ax.set_ylim(0, max(ratios) * 1.25)
                
                # 添加数据标签
                for bar, ratio in zip(bars, ratios):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + max(ratios)*0.02,
                           f'{ratio:.2f}%', ha='center', va='bottom', fontsize=11,
                           fontweight='bold', color=COLOR_PALETTE['dark'])
                
                # 添加分析说明
                total_engagement = like_ratio + comment_ratio + favorite_ratio + share_ratio
                analysis_text = (f"总参与度: {total_engagement:.2f}%\n"
                               f"播放量: {int(play_count):,}\n"
                               f"点赞率最高: {max(ratios):.2f}% ({categories[ratios.index(max(ratios))]})")
                
                plt.figtext(0.5, 0.01, analysis_text, ha='center', fontsize=10,
                           bbox=dict(boxstyle='round', facecolor='#ecf0f1', alpha=0.8))
                
                plt.tight_layout(rect=[0, 0.05, 1, 0.95])
                
                # 保存图表
                safe_filename = "".join(c for c in video_identifier if c.isalnum() or c in (' ', '_', '-')).rstrip()
                safe_filename = safe_filename[:50] if len(safe_filename) > 50 else safe_filename
                output_filename = f"视频互动分析_{safe_filename}.png"
                output_path = os.path.join(chart_dir, output_filename)
                plt.savefig(output_path, dpi=300, bbox_inches='tight')
                print(f"    图表已保存: {output_path}")
                
                plt.close()
                
        except Exception as e:
            print(f"  处理文件 {video_csv_file} 时出错: {e}")
            continue

# ============================================================================
# 1*. 分析所有视频互动数据的平均值
# ============================================================================

def analyze_video_average_engagement():
    """分析所有视频的平均用户参与度"""
    print("\n" + "="*60)
    print("1. 视频互动数据分析（整体平均）")
    print("="*60)

    video_dir = os.path.join('data', 'video')
    video_csv_files = [f for f in os.listdir(video_dir) if f.endswith('_视频.csv')]

    if not video_csv_files:
        print(f"警告：{video_dir} 中未找到 *_视频.csv 文件")
        return

    # ===== 汇总容器 =====
    all_like_ratios = []
    all_comment_ratios = []
    all_favorite_ratios = []
    all_share_ratios = []

    for video_csv_file in video_csv_files:
        video_file_path = os.path.join(video_dir, video_csv_file)
        print(f"处理文件: {video_csv_file}")

        try:
            video_df = pd.read_csv(video_file_path)

            required_columns = ['精确播放数', '点赞数', '评论数', '收藏人数', '转发人数']
            if any(col not in video_df.columns for col in required_columns):
                print(f"  跳过：缺少必要列")
                continue

            for _, row in video_df.iterrows():
                play = float(row['精确播放数']) if not pd.isna(row['精确播放数']) else 0
                if play <= 0:
                    continue

                epsilon = 1e-10
                all_like_ratios.append(row['点赞数'] / (play + epsilon) * 100)
                all_comment_ratios.append(row['评论数'] / (play + epsilon) * 100)
                all_favorite_ratios.append(row['收藏人数'] / (play + epsilon) * 100)
                all_share_ratios.append(row['转发人数'] / (play + epsilon) * 100)

        except Exception as e:
            print(f"  处理失败: {e}")
            continue

    if not all_like_ratios:
        print("未能收集到有效视频数据")
        return

    # ===== 计算平均值 =====
    avg_ratios = [
        np.mean(all_like_ratios),
        np.mean(all_comment_ratios),
        np.mean(all_favorite_ratios),
        np.mean(all_share_ratios)
    ]

    categories = ['点赞比例', '评论比例', '收藏比例', '转发比例']

    # ===== 画图 =====
    fig, ax = create_style_plot(
        '样本视频整体用户参与度平均结构',
        figsize=(10, 6)
    )

    bars = ax.bar(
        categories,
        avg_ratios,
        color=[
            COLOR_PALETTE['primary'],
            COLOR_PALETTE['secondary'],
            COLOR_PALETTE['tertiary'],
            COLOR_PALETTE['quaternary']
        ],
        edgecolor='white',
        linewidth=2
    )

    ax.set_ylabel('平均占播放量比例 (%)', fontsize=12)
    ax.set_ylim(0, max(avg_ratios) * 1.3)

    # 数值标注
    for bar, ratio in zip(bars, avg_ratios):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(avg_ratios) * 0.03,
            f'{ratio:.2f}%',
            ha='center',
            va='bottom',
            fontsize=11,
            fontweight='bold'
        )

    # 说明文字
    plt.figtext(
        0.5,
        0.01,
        f"统计视频数：{len(all_like_ratios)}",
        ha='center',
        fontsize=10,
        bbox=dict(boxstyle='round', facecolor='#ecf0f1', alpha=0.8)
    )

    plt.tight_layout(rect=[0, 0.05, 1, 0.95])

    output_path = os.path.join(chart_dir, '视频整体用户参与度平均.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"图表已保存: {output_path}")

# ============================================================================
# 2. 分析评论用户的参与结构与集中度
# ============================================================================

def analyze_comment_structure():
    """分析评论用户的参与结构与集中度"""
    print("\n" + "="*60)
    print("2. 评论用户参与结构与集中度分析")
    print("="*60)
    
    comment_dir = os.path.join('data', 'comment')
    if not os.path.isdir(comment_dir):
        print(f"找不到目录: {comment_dir}")
        return
    
    csv_files = [f for f in os.listdir(comment_dir) if f.endswith('_评论.csv')]
    if not csv_files:
        print(f"{comment_dir} 中未找到 *_评论.csv 文件")
        return
    
    csv_file = os.path.join(comment_dir, csv_files[0])
    print(f"读取评论文件: {csv_file}")
    
    df = pd.read_csv(csv_file)
    username_col = '用户名' if '用户名' in df.columns else '用户昵称'
    
    # 2.1 基础统计
    user_comment_counts = df.groupby(username_col).size().sort_values(ascending=False)
    total_users = len(user_comment_counts)
    total_comments = len(df)
    
    print(f"\n基础统计:")
    print(f"  发表评论的用户总数: {total_users}")
    print(f"  评论总数: {total_comments}")
    print(f"  平均每个用户评论数: {user_comment_counts.mean():.2f}")
    print(f"  用户评论数中位数: {user_comment_counts.median()}")
    
    # 2.2 用户参与程度饼状图
    def classify_user_by_comments(count):
        if count == 1:
            return '仅评论1条'
        elif 2 <= count <= 5:
            return '评论1-5条'
        else:
            return '评论5条以上'
    
    user_categories = user_comment_counts.map(classify_user_by_comments)
    category_counts = user_categories.value_counts()
    
    fig, ax = create_style_plot('用户评论参与程度分布', figsize=(10, 8))
    
    colors = [COLOR_PALETTE['primary'], COLOR_PALETTE['secondary'], COLOR_PALETTE['tertiary']]
    wedges, texts, autotexts = ax.pie(category_counts.values, 
                                      labels=category_counts.index,
                                      autopct='%1.1f%%',
                                      colors=colors,
                                      startangle=90,
                                      textprops={'fontsize': 11})
    
    # 美化百分比文本
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(10)
    
    # 添加图例
    legend_labels = [f'{label} ({count}人, {count/total_users*100:.1f}%)' 
                    for label, count in zip(category_counts.index, category_counts.values)]
    ax.legend(wedges, legend_labels, title="用户分类", loc="center left", 
              bbox_to_anchor=(1, 0, 0.5, 1), fontsize=10)
    
    plt.tight_layout()
    output_path = os.path.join(chart_dir, '用户参与程度饼状图.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"图表已保存: {output_path}")
    plt.close()
    
    return df, user_comment_counts, total_users, total_comments

# ============================================================================
# 3. 验证"二八定律" - 帕累托图
# ============================================================================

def create_pareto_chart(user_comment_counts, total_comments):
    """创建帕累托图验证二八定律"""
    print("\n" + "="*60)
    print("3. 二八定律验证 - 帕累托图")
    print("="*60)
    
    # 按评论数排序
    sorted_counts = user_comment_counts.sort_values(ascending=False).reset_index(drop=True)
    n_users = len(sorted_counts)
    
    # 计算累积评论比例
    cumulative_ratio = sorted_counts.cumsum() / total_comments * 100
    user_percentage = np.arange(1, n_users + 1) / n_users * 100
    
    fig, ax1 = create_style_plot('用户评论分布帕累托图（二八定律验证）', figsize=(12, 7))
    
    # 绘制累积评论比例曲线
    color1 = COLOR_PALETTE['primary']
    ax1.plot(user_percentage, cumulative_ratio, color=color1, linewidth=3, 
             label='累积评论比例', zorder=5)
    
    # 添加80/20参考线
    ax1.axhline(y=80, color=COLOR_PALETTE['tertiary'], linestyle='--', linewidth=2, 
                alpha=0.7, label='80%参考线')
    ax1.axvline(x=20, color=COLOR_PALETTE['secondary'], linestyle='--', linewidth=2, 
                alpha=0.7, label='20%用户参考线')
    
    # 标记交点
    idx_20 = int(n_users * 0.2)
    ratio_at_20 = cumulative_ratio.iloc[idx_20-1] if idx_20 > 0 else 0
    
    # 找到达到80%评论的用户比例
    users_for_80 = 0
    user_pct_for_80 = 0
    if any(cumulative_ratio >= 80):
        users_for_80 = np.where(cumulative_ratio >= 80)[0][0] + 1
        user_pct_for_80 = users_for_80 / n_users * 100
    
    ax1.scatter([20], [ratio_at_20], color='red', s=100, zorder=10, 
                label=f'20%用户贡献点: {ratio_at_20:.1f}%')
    
    # 标记80%评论点
    if users_for_80 > 0:
        ax1.scatter([user_pct_for_80], [80], color='orange', s=100, zorder=10,
                   label=f'80%评论所需点: {user_pct_for_80:.1f}%用户')
    
    ax1.set_xlabel('累积用户百分比 (%)', fontsize=12)
    ax1.set_ylabel('累积评论比例 (%)', fontsize=12, color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, 100)
    ax1.set_xticks(np.arange(0, 101, 10))
    ax1.set_yticks(np.arange(0, 101, 10))
    
    # 创建第二个y轴用于显示评论数量分布
    ax2 = ax1.twinx()
    color2 = COLOR_PALETTE['gray']
    
    # 绘制用户评论数分布（前100个用户）
    top_n = min(100, n_users)
    ax2.bar(range(1, top_n+1), sorted_counts.head(top_n).values, 
            alpha=0.3, color=color2, label='用户评论数分布')
    
    ax2.set_ylabel('评论数量', fontsize=12, color=color2)
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.set_xlim(0, top_n)
    
    # 合并图例 - 调整图例位置以避免重叠
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    
    # 重新排列图例，将重要的图例项放在前面
    # 创建一个新的图例，手动调整项目顺序
    all_lines = lines1 + lines2
    all_labels = labels1 + labels2
    
    # 创建自定义图例位置，放在图表左上角，避免与右下角的分析文本重叠
    ax1.legend(all_lines, all_labels, loc='upper left', fontsize=9, 
              bbox_to_anchor=(0.02, 0.98), borderaxespad=0., framealpha=0.9)
    
    # 添加分析文本 - 放在图表右下角，但要确保不与图例重叠
    if ratio_at_20 >= 70:
        conclusion = "符合二八定律"
    elif ratio_at_20 >= 60:
        conclusion = "部分符合二八定律"
    else:
        conclusion = "不符合二八定律"
    
    analysis_text = (f"分析结果:\n"
                    f"• 前20%用户贡献了 {ratio_at_20:.1f}% 的评论\n"
                    f"• 达到80%评论需要前 {user_pct_for_80:.1f}% 用户\n"
                    f"• 结论: {conclusion}")
    
    # 将分析文本放在图表右下方，但要确保与图例不重叠
    # 使用bbox_to_anchor定位，放在图表内部右下方
    ax1.text(0.98, 0.12, analysis_text, transform=ax1.transAxes, 
            fontsize=10, verticalalignment='bottom', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
            zorder=10)
    
    # 调整布局，确保所有元素可见
    plt.tight_layout()
    
    output_path = os.path.join(chart_dir, '帕累托图_二八定律验证.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"图表已保存: {output_path}")
    plt.close()

# ============================================================================
# 4. 洛伦兹曲线与基尼系数
# ============================================================================

def create_lorenz_curve(user_comment_counts):
    """创建洛伦兹曲线并计算基尼系数"""
    print("\n" + "="*60)
    print("4. 评论分布不平等性分析 - 洛伦兹曲线与基尼系数")
    print("="*60)
    
    # 按评论数排序（从低到高）
    sorted_counts = user_comment_counts.sort_values()
    n_users = len(sorted_counts)
    
    # 计算累积用户比例和累积评论比例
    user_cumulative = np.arange(1, n_users + 1) / n_users
    comment_cumulative = sorted_counts.cumsum() / sorted_counts.sum()
    
    # 创建一个从高到低排序的版本用于帕累托对比
    sorted_counts_desc = user_comment_counts.sort_values(ascending=False)
    user_cumulative_desc = np.arange(1, n_users + 1) / n_users
    comment_cumulative_desc = sorted_counts_desc.cumsum() / sorted_counts_desc.sum()
    
    # 计算基尼系数
    gini = 0
    for i in range(1, n_users):
        gini += user_cumulative[i] * comment_cumulative[i-1] - user_cumulative[i-1] * comment_cumulative[i]
    
    # 创建平滑的洛伦兹曲线
    x_smooth = np.linspace(0, 1, 300)
    spl = make_interp_spline(user_cumulative, comment_cumulative, k=3)
    y_smooth = spl(x_smooth)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))
    
    # 子图1：洛伦兹曲线
    ax1.set_facecolor('#f8f9fa')
    ax1.plot([0, 1], [0, 1], '--', color=COLOR_PALETTE['gray'], linewidth=2, 
            label='绝对平等线', alpha=0.7)
    ax1.plot(x_smooth, y_smooth, color=COLOR_PALETTE['primary'], linewidth=3, 
            label=f'洛伦兹曲线 (基尼系数: {gini:.3f})')
    ax1.fill_between(x_smooth, x_smooth, y_smooth, alpha=0.3, color=COLOR_PALETTE['primary'])
    
    # 标记关键点
    for percent in [20, 50, 80]:
        idx = int(n_users * percent / 100) - 1
        if idx >= 0:
            # 在洛伦兹曲线中，我们标注的是从低到高排序的用户
            ax1.scatter(user_cumulative[idx], comment_cumulative[idx], 
                      color=COLOR_PALETTE['tertiary'], s=80, zorder=5)
            ax1.annotate(f'{percent}%用户\n贡献{comment_cumulative[idx]*100:.1f}%', 
                       xy=(user_cumulative[idx], comment_cumulative[idx]),
                       xytext=(10, 10), textcoords='offset points',
                       fontsize=9, fontweight='bold')
    
    ax1.set_xlabel('累积用户比例 (%)', fontsize=12)
    ax1.set_ylabel('累积评论比例 (%)', fontsize=12)
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.set_xticks(np.arange(0, 1.1, 0.1))
    ax1.set_yticks(np.arange(0, 1.1, 0.1))
    ax1.xaxis.set_major_formatter(PercentFormatter(1))
    ax1.yaxis.set_major_formatter(PercentFormatter(1))
    ax1.legend(loc='upper left', fontsize=11)
    ax1.set_title('洛伦兹曲线', fontsize=14, fontweight='bold', pad=15)
    ax1.grid(True, alpha=0.3, linestyle='--')
    
    # 子图2：对比帕累托图的关键数据点
    ax2.set_facecolor('#f8f9fa')
    
    # 计算不同百分比用户的实际贡献（从高到低排序）
    percentages = [1, 5, 10, 20, 30, 50, 80]
    user_percents = []
    comment_percents = []
    
    for percent in percentages:
        idx = int(n_users * percent / 100) - 1
        if idx >= 0:
            user_percents.append(percent)
            comment_percents.append(comment_cumulative_desc[idx] * 100)
    
    bars = ax2.bar(range(len(user_percents)), comment_percents, 
                  color=COLOR_PALETTE['secondary'], alpha=0.7)
    
    # 添加数据标签
    for i, (bar, user_pct, comment_pct) in enumerate(zip(bars, user_percents, comment_percents)):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{comment_pct:.1f}%', ha='center', va='bottom', fontsize=9)
        ax2.text(bar.get_x() + bar.get_width()/2., -5,
                f'前{user_pct}%', ha='center', va='top', fontsize=9)
    
    ax2.set_xlabel('用户分组', fontsize=12)
    ax2.set_ylabel('评论贡献比例 (%)', fontsize=12)
    ax2.set_title('不同用户分组评论贡献对比', fontsize=14, fontweight='bold', pad=15)
    ax2.set_xticks([])
    ax2.set_ylim(0, max(comment_percents) * 1.2)
    ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    # 添加80%和20%参考线
    if 20 in user_percents:
        idx_20 = user_percents.index(20)
        ax2.axhline(y=comment_percents[idx_20], color=COLOR_PALETTE['tertiary'], 
                   linestyle='--', alpha=0.5, linewidth=1)
    
    plt.suptitle('评论分布不平等性分析 - 洛伦兹曲线与基尼系数', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    # 打印关键数据点对比
    print(f"\n关键数据点对比:")
    if 20 in user_percents:
        idx_20 = user_percents.index(20)
        print(f"  帕累托图显示: 前20%用户贡献了 {comment_percents[idx_20]:.1f}% 的评论")
    if 80 in user_percents:
        idx_80 = user_percents.index(80)
        print(f"  洛伦兹曲线显示: 后20%用户（最不活跃的20%）贡献了 {100-comment_percents[idx_80]:.1f}% 的评论")
    
    output_path = os.path.join(chart_dir, '洛伦兹曲线_基尼系数.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"图表已保存: {output_path}")
    print(f"基尼系数计算结果: {gini:.3f}")
    plt.close()
    
    return gini

# ============================================================================
# 5. 用户评论数量分布的多角度分析
# ============================================================================

def analyze_comment_distribution(user_comment_counts):
    """
    使用直方图（原始尺度 + 对数尺度）与箱线图
    分析用户评论数量分布形态
    """
    print("\n" + "="*60)
    print("5. 用户评论数量分布的多角度分析 - 分析用户评论数量分布形态")
    print("="*60)

    values = user_comment_counts.values

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    # ---------- 1. 原始尺度直方图 ----------
    axes[0].hist(values, bins=30, color=COLOR_PALETTE['primary'],
                 edgecolor='white', alpha=0.7)
    axes[0].set_title("用户评论数量分布（原始尺度）", fontsize=13)
    axes[0].set_xlabel("评论数量")
    axes[0].set_ylabel("用户数")
    axes[0].grid(True, alpha=0.3, linestyle='--')

    # ---------- 2. 对数尺度直方图 ----------
    axes[1].hist(values, bins=30, color=COLOR_PALETTE['secondary'],
                 edgecolor='white', alpha=0.7)
    axes[1].set_xscale("log")
    axes[1].set_title("用户评论数量分布（对数尺度）", fontsize=13)
    axes[1].set_xlabel("评论数量（log）")
    axes[1].set_ylabel("用户数")
    axes[1].grid(True, alpha=0.3, linestyle='--')

    # ---------- 3. 箱线图 ----------
    axes[2].boxplot(values, vert=True, showfliers=False,
                    patch_artist=True,
                    boxprops=dict(facecolor=COLOR_PALETTE['tertiary']))
    axes[2].set_title("用户评论数量箱线图（隐藏极端值）", fontsize=13)
    axes[2].set_ylabel("评论数量")
    axes[2].grid(True, alpha=0.3, linestyle='--')

    plt.suptitle("用户评论数量分布形态分析", fontsize=16, fontweight='bold')
    plt.tight_layout()

    output_path = os.path.join(chart_dir, "用户评论数量分布_直方图_箱线图.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"图表已保存: {output_path}")

# ============================================================================
# 6. 评论集中度随时间变化分析
# ============================================================================

def analyze_top_user_contribution_by_time(df):
    """
    不同时间阶段 Top 10% 用户评论贡献占比（柱状图）
    用于分析评论集中度随时间的变化
    """
    print("\n" + "="*60)
    print("6. 评论集中度随时间变化分析")
    print("="*60)

    if '评论时间' not in df.columns:
        print("缺少评论时间字段，无法分析评论集中度")
        return

    user_col = '用户ID' if '用户ID' in df.columns else 'uid'
    time_col = '评论时间'

    df[time_col] = pd.to_datetime(df[time_col])
    start_time = df[time_col].min()

    time_stages = {
        '首日': start_time + pd.Timedelta(days=1),
        '前三日': start_time + pd.Timedelta(days=3),
        '首周': start_time + pd.Timedelta(days=7),
        '全部时间': df[time_col].max()
    }

    stage_labels = []
    contribution_ratios = []

    for stage, end_time in time_stages.items():
        subset = df[df[time_col] <= end_time]
        if subset.empty:
            continue

        user_counts = subset.groupby(user_col).size()
        top_n = max(1, int(len(user_counts) * 0.1))
        ratio = user_counts.nlargest(top_n).sum() / len(subset) * 100

        stage_labels.append(stage)
        contribution_ratios.append(ratio)

    # ===== 绘制柱状图 =====
    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.bar(stage_labels, contribution_ratios)

    ax.set_title("不同时间阶段 Top 10% 用户评论贡献占比")
    ax.set_ylabel("评论贡献占比 (%)")
    ax.set_ylim(0, max(contribution_ratios) * 1.2)

    for bar, value in zip(bars, contribution_ratios):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{value:.1f}%",
                ha='center', va='bottom')

    plt.tight_layout()
    
    output_path = os.path.join(chart_dir, "不同时间阶段_Top10%用户评论贡献占比.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"图表已保存：{output_path}")
    plt.close()

# ============================================================================
# 7. 评论数量随时间变化分析
# ============================================================================

def analyze_concentration_over_time(df):
    """分析评论集中度随时间变化"""
    print("\n" + "="*60)
    print("6. 评论集中度随时间变化分析")
    print("="*60)
    
    if '评论时间' not in df.columns:
        print("警告：数据中没有'评论时间'列，跳过时间分析")
        return
    
    username_col = '用户名' if '用户名' in df.columns else '用户昵称'
    
    # 转换时间格式
    df['评论时间'] = pd.to_datetime(df['评论时间'])
    
    # 计算时间跨度（天数）
    time_span = (df['评论时间'].max() - df['评论时间'].min()).days
    
    # 根据时间跨度动态选择时间间隔
    if time_span > 180:  # 超过半年，按月分组
        df['时间分组'] = df['评论时间'].dt.to_period('M')
        freq_label = '月'
    elif time_span > 30:  # 超过一个月，按周分组
        df['时间分组'] = df['评论时间'].dt.to_period('W')
        freq_label = '周'
    elif time_span > 7:  # 超过一周，按天分组
        df['时间分组'] = df['评论时间'].dt.date
        freq_label = '天'
    else:  # 一周以内，按小时分组
        df['时间分组'] = df['评论时间'].dt.floor('h')
        freq_label = '小时'
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # 子图1：前10%用户评论占比随时间变化（改进的时间处理）
    ax1.set_facecolor('#f8f9fa')
    
    # 按时间分组计算集中度
    time_groups = sorted(df['时间分组'].unique())
    
    concentrations = []
    time_labels = []
    
    for time_group in time_groups:
        mask = df['时间分组'] == time_group
        group_data = df[mask]
        
        if len(group_data) > 0:
            user_counts = group_data.groupby(username_col).size()
            total_comments = len(group_data)
            
            if len(user_counts) >= 10:  # 至少有10个用户才计算
                top_10_percent = max(1, int(np.ceil(len(user_counts) * 0.1)))
                top_users = user_counts.nlargest(top_10_percent)
                top_comments = top_users.sum()
                concentration = top_comments / total_comments * 100
                
                concentrations.append(concentration)
                time_labels.append(time_group)
    
    if concentrations:
        ax1.plot(range(len(time_labels)), concentrations, 'o-', color=COLOR_PALETTE['primary'], 
                 linewidth=2, markersize=6, markerfacecolor='white', markeredgewidth=2)
        
        ax1.set_title(f'前10%用户评论占比随时间变化（按{freq_label}）', fontsize=13, fontweight='bold', pad=10)
        ax1.set_xlabel(f'时间（{freq_label}）', fontsize=11)
        ax1.set_ylabel('前10%用户评论占比 (%)', fontsize=11)
        ax1.grid(True, alpha=0.3, linestyle='--')
        
        # 设置x轴刻度
        if len(time_labels) > 10:
            step = max(1, len(time_labels) // 10)
            visible_labels = [str(label) if i % step == 0 else '' for i, label in enumerate(time_labels)]
            ax1.set_xticks(range(len(time_labels)))
            ax1.set_xticklabels(visible_labels, rotation=45, ha='right')
        else:
            ax1.set_xticks(range(len(time_labels)))
            ax1.set_xticklabels([str(label) for label in time_labels], rotation=45, ha='right')
        
        # 添加趋势线
        if len(concentrations) > 3:
            indices = np.arange(len(concentrations))
            z = np.polyfit(indices, concentrations, 1)
            p = np.poly1d(z)
            ax1.plot(indices, p(indices), '--', color=COLOR_PALETTE['tertiary'], 
                     linewidth=2, alpha=0.7, label=f'趋势线')
            ax1.legend(fontsize=10)
        
        # 计算集中度变化
        if len(concentrations) >= 2:
            change_pct = ((concentrations[-1] - concentrations[0]) / concentrations[0] * 100) if concentrations[0] > 0 else 0
            ax1.text(0.02, 0.98, f'集中度变化: {change_pct:+.1f}%', transform=ax1.transAxes,
                    fontsize=10, verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # 子图2：评论总数随时间变化
    ax2.set_facecolor('#f8f9fa')
    
    # 统计每个时间段的评论总数
    comment_counts = df.groupby('时间分组').size()
    
    if len(comment_counts) > 0:
        # 转换为列表保持顺序
        time_labels_total = []
        counts_list = []
        
        for time_group in time_groups:
            if time_group in comment_counts.index:
                time_labels_total.append(time_group)
                counts_list.append(comment_counts[time_group])
        
        ax2.plot(range(len(time_labels_total)), counts_list, 'o-', color=COLOR_PALETTE['secondary'], 
                 linewidth=2, markersize=4, markerfacecolor='white', markeredgewidth=2)
        
        ax2.set_title(f'评论总数随时间变化（按{freq_label}）', fontsize=13, fontweight='bold', pad=10)
        ax2.set_xlabel(f'时间（{freq_label}）', fontsize=11)
        ax2.set_ylabel('评论数量', fontsize=11)
        ax2.grid(True, alpha=0.3, linestyle='--')
        
        # 设置x轴刻度
        if len(time_labels_total) > 10:
            step = max(1, len(time_labels_total) // 10)
            visible_labels = [str(label) if i % step == 0 else '' for i, label in enumerate(time_labels_total)]
            ax2.set_xticks(range(len(time_labels_total)))
            ax2.set_xticklabels(visible_labels, rotation=45, ha='right')
        else:
            ax2.set_xticks(range(len(time_labels_total)))
            ax2.set_xticklabels([str(label) for label in time_labels_total], rotation=45, ha='right')
        
        # 添加总评论数
        total_comments = sum(counts_list)
        ax2.text(0.02, 0.98, f'总评论数: {total_comments:,}', transform=ax2.transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # 标记峰值
        if counts_list:
            peak_idx = counts_list.index(max(counts_list))
            peak_value = counts_list[peak_idx]
            ax2.scatter([peak_idx], [peak_value], color='red', s=100, zorder=5)
            ax2.annotate(f'峰值: {peak_value}', xy=(peak_idx, peak_value),
                        xytext=(10, 10), textcoords='offset points',
                        fontsize=9, fontweight='bold')
    
    plt.suptitle(f'评论集中度与评论数量时间变化分析（按{freq_label}）', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    output_path = os.path.join(chart_dir, '评论集中度时间变化.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"图表已保存: {output_path}")
    plt.close()
    
    # 打印时间分析结果
    print(f"\n时间分析结果:")
    print(f"  时间跨度: {time_span} 天")
    print(f"  分析粒度: 按{freq_label}")
    if concentrations:
        print(f"  前10%用户评论占比范围: {min(concentrations):.1f}% - {max(concentrations):.1f}%")
        print(f"  平均集中度: {np.mean(concentrations):.1f}%")

# ============================================================================
# 8. 评论关键词及情感趋势分析
# ============================================================================

def analyze_keywords_and_sentiment(df, video_title_prefix=None):
    """分析评论关键词及情感趋势
    video_title_prefix: 视频标题前两个字，用于加载对应的自定义词典
    """
    print("\n" + "=" * 60)
    print("8. 评论关键词及情感趋势分析")
    print("=" * 60)

    if '评论内容' not in df.columns:
        print("警告：数据中没有'评论内容'列，跳过关键词分析")
        return

    # ==================== jieba 词典加载 ====================
    dict_loaded = False
    if video_title_prefix and isinstance(video_title_prefix, str) and len(video_title_prefix) >= 2:
        dict_filename = f"bili_dict/{video_title_prefix[:2]}.txt"
        if os.path.exists(dict_filename):
            try:
                jieba.load_userdict(dict_filename)
                dict_loaded = True
                print(f"已加载自定义词典: {dict_filename}")
            except Exception as e:
                print(f"自定义词典加载失败: {e}")

    if not dict_loaded:
        basic_bili_words = [
            "一键三连", "UP主", "破防", "弹幕", "投币",
            "充电", "关注", "收藏", "白嫖", "离谱"
        ]
        for w in basic_bili_words:
            jieba.add_word(w)
        print("使用基础 B 站词汇词典")

    # ==================== 停用词 & 分词函数 ====================
    stop_words = set([
        '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一',
        '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着',
        '没有', '看', '好', '自己', '这', '视频', '哈哈', '回复', '我们',
        '你们', '不是', '就是', '什么', '播放', 'doge', '孤泳者', '这个',
        '怎么', '现在'
    ])

    def extract_keywords(text):
        if pd.isna(text):
            return []
        words = jieba.lcut(str(text))
        return [w for w in words if len(w) > 1 and w not in stop_words]

    # ==================== 关键词统计 ====================
    all_keywords = []
    for c in df['评论内容'].dropna():
        all_keywords.extend(extract_keywords(c))

    word_freq = Counter(all_keywords)
    top_words = word_freq.most_common(10)

    print("\n高频词统计（前10）:")
    for i, (w, f) in enumerate(top_words, 1):
        print(f"{i:2d}. {w}: {f}")

    # =========================================================================
    # 图 1：高频词比例饼状图（显示“次数 + 百分比”）
    # =========================================================================
    fig1, ax1 = plt.subplots(figsize=(7, 7))
    ax1.set_facecolor('#f8f9fa')

    words, freqs = zip(*top_words)
    total = sum(freqs)

    def autopct_fmt(pct):
        count = int(round(pct * total / 100))
        return f"{count}\n({pct:.1f}%)"

    colors = plt.cm.Set3(np.linspace(0, 1, len(words)))
    ax1.pie(
        freqs,
        labels=words,
        autopct=autopct_fmt,
        startangle=90,
        colors=colors,
        textprops={'fontsize': 10}
    )

    dict_info = video_title_prefix[:2] if (video_title_prefix and dict_loaded) else "基础"
    ax1.set_title(f"评论高频词分布（词典：{dict_info}）", fontsize=14, fontweight='bold')

    plt.tight_layout()
    output_path = os.path.join(chart_dir, "评论高频词比例饼状图.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"图表已保存: {output_path}")

    # =========================================================================
    # 图 2：各时间段 Top5 高频词的评论数量变化（词汇可动态进出）
    # =========================================================================
    if '评论时间' not in df.columns:
        print("缺少评论时间字段，跳过时间趋势分析")
        return

    df_time = df.copy()
    df_time['评论时间'] = pd.to_datetime(df_time['评论时间'])

    # ---------- 时间分组 ----------
    time_span = (df_time['评论时间'].max() - df_time['评论时间'].min()).days

    if time_span > 180:
        df_time['时间分组'] = df_time['评论时间'].dt.to_period('M')
        freq_label = '月'
    elif time_span > 30:
        df_time['时间分组'] = df_time['评论时间'].dt.to_period('W')
        freq_label = '周'
    elif time_span > 7:
        df_time['时间分组'] = df_time['评论时间'].dt.date
        freq_label = '天'
    else:
        df_time['时间分组'] = df_time['评论时间'].dt.floor('h')
        freq_label = '小时'

    time_groups = sorted(df_time['时间分组'].unique())

    # ---------- 每个时间段的 Top5 词 ----------
    period_top_words = {}   # {time: Counter}
    all_top_words = set()   # 所有出现过的 Top5 词

    for tg in time_groups:
        comments = df_time[df_time['时间分组'] == tg]['评论内容'].dropna()
        keywords = []
        for c in comments:
            keywords.extend(extract_keywords(c))

        freq = Counter(keywords)
        top5 = dict(freq.most_common(5))

        period_top_words[tg] = top5
        all_top_words.update(top5.keys())

    all_top_words = sorted(all_top_words)

    # ---------- 构建时间序列 ----------
    word_trends = {word: [] for word in all_top_words}

    for tg in time_groups:
        freq_dict = period_top_words.get(tg, {})
        for word in all_top_words:
            word_trends[word].append(freq_dict.get(word, 0))

    # ---------- 绘图（横向拉伸 + 图例下移） ----------
    fig, ax = plt.subplots(figsize=(16, 5))  # 宽↑ 高↓

    colors = plt.cm.tab20(np.linspace(0, 1, len(all_top_words)))

    for word, color in zip(all_top_words, colors):
        if any(word_trends[word]):
            ax.plot(
                range(len(time_groups)),
                word_trends[word],
                marker='o',
                linewidth=2,
                markersize=4,
                label=word,
                color=color
            )

    ax.set_title(
        f"各时间段 Top5 高频词评论数量变化（按{freq_label}）",
        fontsize=14,
        fontweight='bold',
        pad=15
    )
    ax.set_xlabel(f"时间（{freq_label}）")
    ax.set_ylabel("评论中出现次数")
    #ax.set_yscale("symlog")

    # ---------- x 轴刻度 ----------
    time_labels = [str(t) for t in time_groups]
    if len(time_labels) > 10:
        step = max(1, len(time_labels) // 10)
        ax.set_xticks(range(len(time_labels)))
        ax.set_xticklabels(
            [t if i % step == 0 else '' for i, t in enumerate(time_labels)],
            rotation=45,
            ha='right'
        )
    else:
        ax.set_xticks(range(len(time_labels)))
        ax.set_xticklabels(time_labels, rotation=45, ha='right')

    ax.grid(True, linestyle='--', alpha=0.35)

    # ---------- 图例放到下方 ----------
    ax.legend(
        title="进入过 Top5 的关键词",
        loc='upper center',
        bbox_to_anchor=(0.5, -0.28),   # 下移
        ncol=5,                        # 每行 5 个词，可自行调
        fontsize=9,
        title_fontsize=10,
        frameon=False
    )

    # 为下方 legend 留空间
    plt.subplots_adjust(bottom=0.32)

    output_path = os.path.join(chart_dir, "高频词时间演化（动态Top5）.png")
    plt.savefig(output_path, dpi=500, bbox_inches='tight')
    plt.close()

    print(f"图表已保存: {output_path}")

# ============================================================================
# 主程序
# ============================================================================

def main():
    """主程序"""
    print("开始数据分析与可视化...")
    
    try:
        # 1. 分析视频互动数据
        #analyze_video_engagement()
        
        # 1*. 分析视频互动数据
        #analyze_video_average_engagement()

        # 2. 分析评论用户参与结构
        df, user_comment_counts, total_users, total_comments = analyze_comment_structure()
        
        # 3. 验证二八定律 - 帕累托图
        #create_pareto_chart(user_comment_counts, total_comments)
        
        # 4. 洛伦兹曲线与基尼系数
        #gini = create_lorenz_curve(user_comment_counts)
        
        # 5. 多角度分布分析
        #analyze_comment_distribution(user_comment_counts)
        
        # 6. 评论集中度时间变化
        #analyze_top_user_contribution_by_time(df)
        
        # 7. 评论数量随时间变化
        #analyze_concentration_over_time(df)

        # 8. 评论关键词及情感趋势
        analyze_keywords_and_sentiment(df)
        
        print("\n" + "="*60)
        print("所有分析完成！图表已保存到 'chart/images' 目录")
        print("="*60)
        
    except Exception as e:
        print(f"\n程序执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
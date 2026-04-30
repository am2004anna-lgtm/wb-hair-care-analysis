import pandas as pd
import matplotlib.pyplot as plt
import mplcursors


def normalize_yes_no(value):
    if pd.isna(value):
        return "нет"
    text = str(value).strip().lower()
    if text in {"да", "д", "yes", "y"}:
        return "да"
    return "нет"


def main():
    file_name = "wb_products.xlsx"
    df = pd.read_excel(file_name)

    # Приводим названия колонок к ожидаемому виду.
    if "Название" in df.columns and "Название (3-4 слова)" not in df.columns:
        df["Название (3-4 слова)"] = df["Название"]

    expected_cols = [
        "Артикул",
        "Название (3-4 слова)",
        "Бренд",
        "Цена, руб",
        "Отзывы",
        "Рейтинг",
        "Видео (да/нет)",
        "Инфографика (да/нет)",
    ]

    for col in expected_cols:
        if col not in df.columns:
            df[col] = None

    df["Цена, руб"] = pd.to_numeric(df["Цена, руб"], errors="coerce")
    df["Отзывы"] = pd.to_numeric(df["Отзывы"], errors="coerce")
    df["Рейтинг"] = pd.to_numeric(df["Рейтинг"], errors="coerce")
    df["Видео (да/нет)"] = df["Видео (да/нет)"].apply(normalize_yes_no)
    df["Инфографика (да/нет)"] = df["Инфографика (да/нет)"].apply(normalize_yes_no)

    valid_df = df.dropna(subset=["Цена, руб", "Отзывы", "Рейтинг"]).copy()

    print("=" * 50)
    print("АНАЛИЗ РЫНКА НЕСМЫВАЕМОГО УХОДА")
    print("=" * 50)
    print(f"Всего строк в таблице: {len(df)}")
    print(f"Строк с полными данными: {len(valid_df)}")
    print(f"Брендов представлено: {df['Бренд'].dropna().nunique()}")

    if len(valid_df) == 0:
        print("Недостаточно числовых данных для расчета метрик и графика.")
        return

    print(f"Средняя цена: {valid_df['Цена, руб'].mean():.0f} руб.")
    print(f"Средний рейтинг: {valid_df['Рейтинг'].mean():.2f}")
    print(f"Среднее количество отзывов: {valid_df['Отзывы'].mean():.0f}")

    max_price = valid_df.loc[valid_df["Цена, руб"].idxmax()]
    min_price = valid_df.loc[valid_df["Цена, руб"].idxmin()]
    print(f"Самый дорогой: {max_price['Название (3-4 слова)']} — {max_price['Цена, руб']:.0f} руб.")
    print(f"Самый дешевый: {min_price['Название (3-4 слова)']} — {min_price['Цена, руб']:.0f} руб.")

    with_inf = valid_df[valid_df["Инфографика (да/нет)"] == "да"]["Рейтинг"]
    without_inf = valid_df[valid_df["Инфографика (да/нет)"] == "нет"]["Рейтинг"]
    if len(with_inf) > 0 and len(without_inf) > 0:
        print(
            f"Инфографика: средний рейтинг {with_inf.mean():.2f} (с инфографикой) "
            f"vs {without_inf.mean():.2f} (без)."
        )
    else:
        print("Недостаточно данных для сравнения влияния инфографики.")

    top_brands = valid_df.groupby("Бренд")["Отзывы"].sum().sort_values(ascending=False)
    print("Топ бренды по сумме отзывов:")
    for brand, reviews in top_brands.head(5).items():
        print(f" - {brand}: {int(reviews)}")

    avg_price = valid_df["Цена, руб"].mean()
    avg_rating = valid_df["Рейтинг"].mean()
    avg_reviews = valid_df["Отзывы"].mean()
    top_brand_name = top_brands.index[0] if len(top_brands) > 0 else "н/д"
    top_brand_reviews = int(top_brands.iloc[0]) if len(top_brands) > 0 else 0

    fig, ax = plt.subplots(figsize=(12, 7))
    artists = []
    for brand, group in valid_df.groupby("Бренд"):
        label = str(brand) if pd.notna(brand) else "Без бренда"
        scatter = ax.scatter(group["Цена, руб"], group["Отзывы"], alpha=0.8, s=90, label=label)
        artists.append((scatter, group.reset_index(drop=True), label))

    ax.set_xlabel("Цена (руб.)")
    ax.set_ylabel("Количество отзывов")
    ax.set_title("Зависимость отзывов от цены")

    summary = (
        f"Всего товаров: {len(valid_df)}\n"
        f"Средняя цена: {avg_price:.0f} руб.\n"
        f"Средний рейтинг: {avg_rating:.2f}\n"
        f"Среднее кол-во отзывов: {avg_reviews:.0f}\n"
        f"Самый дорогой: {max_price['Цена, руб']:.0f} руб.\n"
        f"Самый дешевый: {min_price['Цена, руб']:.0f} руб.\n"
        f"Топ бренд: {top_brand_name} ({top_brand_reviews} отзывов)"
    )
    fig.text(
        0.71,
        0.18,
        summary,
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.5", "facecolor": "#f5f5f5", "edgecolor": "#999999"},
    )

    ax.grid(True, alpha=0.3)
    ax.legend(title="Бренды", fontsize=8, title_fontsize=9, loc="upper left", bbox_to_anchor=(1.01, 1))
    fig.tight_layout(rect=(0, 0, 0.82, 1))
    fig.savefig("analiz_nesmyvashki.png", dpi=150)

    for scatter, group, label in artists:
        cursor = mplcursors.cursor(scatter, hover=2)

        @cursor.connect("add")
        def on_add(sel, group=group, label=label):
            i = sel.index
            row = group.iloc[i]
            sel.annotation.set_text(
                f"Бренд: {label}\n"
                f"Цена: {row['Цена, руб']:.0f} руб.\n"
                f"Отзывы: {row['Отзывы']:.0f}"
            )
            sel.annotation.get_bbox_patch().set(alpha=0.9)

    plt.show()

    print("=" * 50)
    print("Анализ завершен. График сохранен как 'analiz_nesmyvashki.png'.")
    print("=" * 50)


if __name__ == "__main__":
    main()

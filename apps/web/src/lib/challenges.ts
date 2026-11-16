export type Challenge = {
  slug: string;
  title: string;
  description: string;
  category: string;
  difficulty: "Легко" | "Средне" | "Сложно";
  time: string;
  budget: string;
  xp: number;
  participants: number;
  deadline: string;
  accent: string;
  imageLabel: string;
  ingredients: string[];
  steps: string[];
};

export const challenges: Challenge[] = [
  {
    slug: "perfect-breakfast",
    title: "Завтрак, который хочется повторить",
    description: "Соберите свой идеальный завтрак: от красивой подачи до сочетания вкусов. Классика или авторская идея — решать вам.",
    category: "Завтраки",
    difficulty: "Легко",
    time: "20–35 мин",
    budget: "до 500 ₽",
    xp: 120,
    participants: 248,
    deadline: "До воскресенья",
    accent: "peach",
    imageLabel: "Идея для завтрака",
    ingredients: ["Яйца или растительная альтернатива", "Сезонные овощи или фрукты", "Основа на выбор: хлеб, крупа или йогурт", "Один неожиданный ингредиент"],
    steps: ["Выберите основу и главный вкус.", "Приготовьте блюдо и продумайте подачу.", "Сделайте фото результата при естественном освещении.", "Опубликуйте работу и расскажите об одной детали, которой гордитесь."],
  },
  {
    slug: "seasonal-vegetables",
    title: "Сезонные овощи — главный герой",
    description: "Покажите, как превратить простые сезонные овощи в блюдо, к которому захочется вернуться.",
    category: "Овощи",
    difficulty: "Средне",
    time: "35–50 мин",
    budget: "до 700 ₽",
    xp: 180,
    participants: 176,
    deadline: "Ещё 3 дня",
    accent: "sage",
    imageLabel: "Сезонные овощи",
    ingredients: ["Не менее двух видов овощей", "Зелень или свежие травы", "Основа или гарнир по желанию", "Специи и соус на ваш вкус"],
    steps: ["Выберите два сезонных овоща.", "Используйте минимум один приём, раскрывающий вкус: запекание, гриль или тушение.", "Соберите блюдо и сделайте фото.", "Опубликуйте результат с коротким комментарием."],
  },
  {
    slug: "comfort-food",
    title: "Домашний comfort food",
    description: "Приготовьте блюдо, которое создаёт ощущение уюта. Важны история, вкус и ваш личный подход.",
    category: "Домашняя кухня",
    difficulty: "Средне",
    time: "40–60 мин",
    budget: "до 900 ₽",
    xp: 160,
    participants: 312,
    deadline: "Ещё 5 дней",
    accent: "plum",
    imageLabel: "Домашняя еда",
    ingredients: ["Любимая домашняя основа", "Один ингредиент с личной историей", "Приправы по вкусу"],
    steps: ["Выберите блюдо, которое ассоциируется с уютом.", "Приготовьте его в своей интерпретации.", "Сфотографируйте готовый результат.", "Поделитесь короткой историей блюда."],
  },
];

export function getChallenge(slug: string) {
  return challenges.find((challenge) => challenge.slug === slug);
}

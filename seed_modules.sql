-- Kunpeng demo seed data
-- 请确保数据库已创建并使用 kunpeng
USE kunpeng;

-- =========================
-- 商品模块（product）
-- =========================

INSERT INTO product_category (name, sort_order) VALUES
  ('转运开光', 1),
  ('招财祈福', 2),
  ('护身平安', 3);

INSERT INTO product (
  name, category_id, price, init_stock, stock, zodiac_flags,
  is_home_show, home_section, main_image, description_html, status
) VALUES
  (
    '开光玉佛（转运）',
    (SELECT id FROM product_category WHERE name='转运开光' LIMIT 1),
    199.00, 100, 100,
    'fortune,career', 1, '热门商品', '/static/demo/product/yubaofo.jpg',
    '玉佛灵光护佑，愿你转运顺遂、事业有成。',
    'on'
  ),
  (
    '祈福金铃（招财）',
    (SELECT id FROM product_category WHERE name='招财祈福' LIMIT 1),
    129.00, 200, 200,
    'wealth,marriage', 1, '转运法宝', '/static/demo/product/jinling.jpg',
    '金铃招财纳福，愿财源广进、福气常在。',
    'on'
  ),
  (
    '平安护符（护身）',
    (SELECT id FROM product_category WHERE name='护身平安' LIMIT 1),
    99.00, 300, 300,
    'health,career', 0, '守护平安', '/static/demo/product/hufu.jpg',
    '护符护你平安常在，心安即是好运。',
    'on'
  ),
  (
    '开运香囊（助学/事业）',
    (SELECT id FROM product_category WHERE name='转运开光' LIMIT 1),
    59.00, 500, 500,
    'study,career', 0, '热门商品', '/static/demo/product/xiangnang.jpg',
    '香囊助运，愿你学习精进、前程坦途。',
    'on'
  );

-- =========================
-- 网上祈福模块（blessing）
-- =========================

INSERT INTO bless_item_category (name) VALUES
  ('常用祈福'),
  ('节庆祈愿');

-- 注意：当前后端 BlessItem 模型未强制使用 category_id/icon，这里仍可插入
INSERT INTO bless_item (name, category_id, icon, price_coin, status) VALUES
  ('观音加持香', (SELECT id FROM bless_item_category WHERE name='常用祈福' LIMIT 1), '', 3, 'on'),
  ('招财好运灯', (SELECT id FROM bless_item_category WHERE name='常用祈福' LIMIT 1), '', 5, 'on'),
  ('新年开运祈愿', (SELECT id FROM bless_item_category WHERE name='节庆祈愿' LIMIT 1), '', 8, 'on');

-- 祈福动态（动态列表会展示 bless_feed.content）
INSERT INTO bless_feed (display_name, bless_item_id, bless_item_name, content, created_by_admin) VALUES
  (
    'Alice',
    (SELECT id FROM bless_item WHERE name='观音加持香' LIMIT 1),
    '观音加持香',
    '愿家人平安喜乐，心想事成。',
    NULL
  ),
  (
    'Bob',
    (SELECT id FROM bless_item WHERE name='招财好运灯' LIMIT 1),
    '招财好运灯',
    '愿财运亨通，贵人相助，项目进展顺利。',
    NULL
  );

-- =========================
-- 网上祭祀模块（memorial/sacrifice）
-- =========================

INSERT INTO offering_category (name) VALUES
  ('传统贡品'),
  ('素食供品');

INSERT INTO offering (name, category_id, icon, price_coin, status) VALUES
  (
    '三牲礼盒',
    (SELECT id FROM offering_category WHERE name='传统贡品' LIMIT 1),
    '',
    10,
    'on'
  ),
  (
    '时令水果盘',
    (SELECT id FROM offering_category WHERE name='素食供品' LIMIT 1),
    '',
    6,
    'on'
  ),
  (
    '祈愿香烛',
    (SELECT id FROM offering_category WHERE name='传统贡品' LIMIT 1),
    '',
    4,
    'on'
  );

-- 陵墓（Cemetery）
INSERT INTO cemetery (
  deceased_name, gender, birthday, death_day, epitaph,
  creator_user_id, creator_account, relation, avatar_url
) VALUES
  (
    '李先贤',
    'male',
    '1955-03-20',
    '2018-11-02',
    '德泽后世，铭记不忘。',
    NULL,
    NULL,
    '父亲',
    '/static/demo/memorial/tomb1.jpg'
  ),
  (
    '王女士',
    'female',
    '1962-07-10',
    '2020-04-18',
    '温柔坚韧，一生善良。',
    NULL,
    NULL,
    '母亲',
    '/static/demo/memorial/tomb2.jpg'
  );

-- 祭祀动态（SacrificeFeed）
INSERT INTO sacrifice_feed (
  user_id, user_mobile, offering_name, deceased_name, relation,
  content, sacrifice_time, created_by_admin
) VALUES
  (
    NULL, '18800001111',
    '祈愿香烛',
    '王女士',
    '母亲',
    '愿您在天安好，愿家人此生顺遂、平安喜乐。',
    NOW(),
    NULL
  ),
  (
    NULL, '18800002222',
    '时令水果盘',
    '李先贤',
    '父亲',
    '愿思念得慰，愿福泽常在，愿日子越过越好。',
    NOW(),
    NULL
  );

-- =========================
-- 内容与教学模块（content + teaching）
-- =========================

-- 内容：文章分类/文章（metaphysics）
INSERT INTO article_category (name) VALUES
  ('风水堪舆'),
  ('命理运势'),
  ('传统文化');

INSERT INTO article (
  title, category_id, cover_image, content_html, status, published_at
) VALUES
  (
    '风水格局入门：看明堂与方位',
    (SELECT id FROM article_category WHERE name='风水堪舆' LIMIT 1),
    '/static/demo/content/article1.jpg',
    '<p>明堂开阔、方位得宜，有助于气场流通与生活顺遂。</p>',
    'published',
    NOW()
  ),
  (
    '八字命理：如何理解五行与调候',
    (SELECT id FROM article_category WHERE name='命理运势' LIMIT 1),
    '/static/demo/content/article2.jpg',
    '<p>五行相生相克，调候得当方能趋吉避凶。</p>',
    'published',
    NOW()
  ),
  (
    '传统文化：择吉与仪式感的意义',
    (SELECT id FROM article_category WHERE name='传统文化' LIMIT 1),
    '/static/demo/content/article3.jpg',
    '<p>择吉与仪式感能帮助人把握节奏，建立信心。</p>',
    'published',
    NOW()
  );

-- 教学：视频/课件/一对一/直播（teaching）
INSERT INTO teach_video (title, cover_image, video_url, status, published_at) VALUES
  ('八字入门：四柱与十神', '/static/demo/teach/v1.jpg', '/static/demo/teach/v1.mp4', 'on', NOW()),
  ('风水实战：客厅布局要点', '/static/demo/teach/v2.jpg', '/static/demo/teach/v2.mp4', 'on', NOW());

INSERT INTO courseware (title, cover_image, file_url, published_at) VALUES
  ('风水堪舆速查手册', '/static/demo/teach/cw1.jpg', '/static/demo/teach/cw1.pdf', NOW()),
  ('八字命理学习资料包', '/static/demo/teach/cw2.jpg', '/static/demo/teach/cw2.pdf', NOW());

INSERT INTO one2one_course (title, image, description_html, expert_id, published_at, status) VALUES
  ('一对一择日择吉辅导', '/static/demo/teach/o2o1.jpg', '<p>根据个人情况提供择日建议。</p>', NULL, NOW(), 'on'),
  ('一对一改名提升运势', '/static/demo/teach/o2o2.jpg', '<p>结合五行与笔画给出命名方向。</p>', NULL, NOW(), 'on');

INSERT INTO live_event (title, live_start, live_end, live_url, status) VALUES
  (
    '周末风水课堂：办公室布局',
    NOW(),
    DATE_ADD(NOW(), INTERVAL 2 HOUR),
    '/static/demo/live/live1.mp4',
    'living'
  );


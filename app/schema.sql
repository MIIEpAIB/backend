CREATE DATABASE IF NOT EXISTS kunpeng
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE kunpeng;

-- ========== 1. 权限与系统管理 ==========

CREATE TABLE admin_user (
  id            BIGINT PRIMARY KEY AUTO_INCREMENT,
  username      VARCHAR(64) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  status        TINYINT NOT NULL DEFAULT 1,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE role (
  id          BIGINT PRIMARY KEY AUTO_INCREMENT,
  name        VARCHAR(64) NOT NULL UNIQUE,
  description VARCHAR(255),
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE admin_user_role (
  admin_id BIGINT NOT NULL,
  role_id  BIGINT NOT NULL,
  PRIMARY KEY (admin_id, role_id),
  CONSTRAINT fk_admin_user_role_admin FOREIGN KEY (admin_id) REFERENCES admin_user(id),
  CONSTRAINT fk_admin_user_role_role  FOREIGN KEY (role_id)  REFERENCES role(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE permission (
  id    BIGINT PRIMARY KEY AUTO_INCREMENT,
  code  VARCHAR(64) NOT NULL UNIQUE,
  name  VARCHAR(128) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE role_permission (
  role_id       BIGINT NOT NULL,
  permission_id BIGINT NOT NULL,
  PRIMARY KEY (role_id, permission_id),
  CONSTRAINT fk_role_perm_role FOREIGN KEY (role_id) REFERENCES role(id),
  CONSTRAINT fk_role_perm_perm FOREIGN KEY (permission_id) REFERENCES permission(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE admin_op_log (
  id          BIGINT PRIMARY KEY AUTO_INCREMENT,
  admin_id    BIGINT NOT NULL,
  username    VARCHAR(64) NOT NULL,
  action      VARCHAR(128) NOT NULL,
  target_type VARCHAR(64),
  target_id   BIGINT,
  detail      JSON,
  ip          VARCHAR(64),
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_oplog_admin FOREIGN KEY (admin_id) REFERENCES admin_user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========== 2. 用户与账户 ==========

CREATE TABLE user (
  id            BIGINT PRIMARY KEY AUTO_INCREMENT,
  mobile        VARCHAR(20) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  nickname      VARCHAR(64),
  source        ENUM('portal','backend') NOT NULL DEFAULT 'portal',
  register_ip   VARCHAR(64),
  registered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_login_at DATETIME,
  balance       DECIMAL(12,2) NOT NULL DEFAULT 0,
  real_name     VARCHAR(64),
  status        TINYINT NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE user_address (
  id            BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id       BIGINT NOT NULL,
  receiver_name VARCHAR(64) NOT NULL,
  mobile        VARCHAR(20) NOT NULL,
  province      VARCHAR(64),
  city          VARCHAR(64),
  district      VARCHAR(64),
  detail_addr   VARCHAR(255),
  is_default    TINYINT NOT NULL DEFAULT 0,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_addr_user FOREIGN KEY (user_id) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE user_bank_card (
  id          BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id     BIGINT NOT NULL,
  bank_name   VARCHAR(64),
  card_last4  VARCHAR(4),
  holder_name VARCHAR(64),
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_card_user FOREIGN KEY (user_id) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE recharge_order (
  id             BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id        BIGINT NOT NULL,
  order_no       VARCHAR(64) NOT NULL UNIQUE,
  amount         DECIMAL(12,2) NOT NULL,
  status         ENUM('pending','success','failed','unknown') NOT NULL DEFAULT 'pending',
  pay_method     ENUM('wechat','alipay','credit_card') NOT NULL,
  channel_txn_id VARCHAR(128),
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  confirmed_by   BIGINT,
  confirmed_at   DATETIME,
  CONSTRAINT fk_recharge_user FOREIGN KEY (user_id) REFERENCES user(id),
  CONSTRAINT fk_recharge_admin FOREIGN KEY (confirmed_by) REFERENCES admin_user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE balance_log (
  id             BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id        BIGINT NOT NULL,
  type           ENUM('recharge','buy_product','online_sacrifice','online_blessing') NOT NULL,
  amount_change  DECIMAL(12,2) NOT NULL,
  balance_before DECIMAL(12,2) NOT NULL,
  balance_after  DECIMAL(12,2) NOT NULL,
  ref_type       VARCHAR(64),
  ref_id         BIGINT,
  remark         VARCHAR(255),
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_balance_user FOREIGN KEY (user_id) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========== 3. 实物商品与订单 ==========

CREATE TABLE product_category (
  id         BIGINT PRIMARY KEY AUTO_INCREMENT,
  name       VARCHAR(64) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE product (
  id              BIGINT PRIMARY KEY AUTO_INCREMENT,
  name            VARCHAR(128) NOT NULL,
  category_id     BIGINT NOT NULL,
  price           DECIMAL(12,2) NOT NULL,
  init_stock      INT NOT NULL,
  stock           INT NOT NULL,
  zodiac_flags    VARCHAR(64),
  is_home_show    TINYINT NOT NULL DEFAULT 0,
  home_section    VARCHAR(32),
  main_image      VARCHAR(255),
  description_html MEDIUMTEXT,
  status          ENUM('on','off') NOT NULL DEFAULT 'on',
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES product_category(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE product_image (
  id         BIGINT PRIMARY KEY AUTO_INCREMENT,
  product_id BIGINT NOT NULL,
  type       ENUM('detail','kaiguang') NOT NULL,
  image_url  VARCHAR(255) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  CONSTRAINT fk_pimg_product FOREIGN KEY (product_id) REFERENCES product(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE product_order (
  id              BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_no        VARCHAR(64) NOT NULL UNIQUE,
  user_id         BIGINT NOT NULL,
  address_id      BIGINT NOT NULL,
  amount_product  DECIMAL(12,2) NOT NULL,
  amount_shipping DECIMAL(12,2) NOT NULL DEFAULT 0,
  amount_total    DECIMAL(12,2) NOT NULL,
  pay_status      ENUM('unpaid','paid') NOT NULL DEFAULT 'unpaid',
  ship_status     ENUM('unshipped','shipped','received') NOT NULL DEFAULT 'unshipped',
  pay_method      ENUM('wechat','alipay','balance') NOT NULL,
  pay_time        DATETIME,
  ship_time       DATETIME,
  receive_time    DATETIME,
  express_company VARCHAR(64),
  tracking_no     VARCHAR(64),
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_porder_user FOREIGN KEY (user_id) REFERENCES user(id),
  CONSTRAINT fk_porder_addr FOREIGN KEY (address_id) REFERENCES user_address(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE product_order_item (
  id            BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_id      BIGINT NOT NULL,
  product_id    BIGINT NOT NULL,
  product_name  VARCHAR(128) NOT NULL,
  category_name VARCHAR(64),
  price         DECIMAL(12,2) NOT NULL,
  quantity      INT NOT NULL,
  amount        DECIMAL(12,2) NOT NULL,
  CONSTRAINT fk_poi_order FOREIGN KEY (order_id) REFERENCES product_order(id),
  CONSTRAINT fk_poi_product FOREIGN KEY (product_id) REFERENCES product(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========== 4. 网上祈福 ==========

CREATE TABLE bless_item_category (
  id         BIGINT PRIMARY KEY AUTO_INCREMENT,
  name       VARCHAR(64) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE bless_item (
  id          BIGINT PRIMARY KEY AUTO_INCREMENT,
  name        VARCHAR(64) NOT NULL,
  category_id BIGINT,
  icon        VARCHAR(255),
  price_coin  INT NOT NULL,
  status      ENUM('on','off') NOT NULL DEFAULT 'on',
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_bless_cat FOREIGN KEY (category_id) REFERENCES bless_item_category(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE bless_order (
  id             BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_no       VARCHAR(64) NOT NULL UNIQUE,
  user_id        BIGINT NOT NULL,
  bless_item_id  BIGINT NOT NULL,
  item_name      VARCHAR(64) NOT NULL,
  price_coin     INT NOT NULL,
  quantity       INT NOT NULL,
  total_coin     INT NOT NULL,
  rmb_amount     DECIMAL(12,2) NOT NULL,
  rate_at_order  DECIMAL(12,4) NOT NULL,
  pay_status     ENUM('unpaid','paid') NOT NULL DEFAULT 'unpaid',
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  paid_at        DATETIME,
  CONSTRAINT fk_bless_order_user FOREIGN KEY (user_id) REFERENCES user(id),
  CONSTRAINT fk_bless_order_item FOREIGN KEY (bless_item_id) REFERENCES bless_item(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE bless_feed (
  id              BIGINT PRIMARY KEY AUTO_INCREMENT,
  display_name    VARCHAR(64) NOT NULL,
  bless_item_id   BIGINT,
  bless_item_name VARCHAR(64),
  content         VARCHAR(512) NOT NULL,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by_admin BIGINT,
  CONSTRAINT fk_bfeed_item FOREIGN KEY (bless_item_id) REFERENCES bless_item(id),
  CONSTRAINT fk_bfeed_admin FOREIGN KEY (created_by_admin) REFERENCES admin_user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========== 5. 网上祭祀 ==========

CREATE TABLE offering_category (
  id         BIGINT PRIMARY KEY AUTO_INCREMENT,
  name       VARCHAR(64) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE offering (
  id          BIGINT PRIMARY KEY AUTO_INCREMENT,
  name        VARCHAR(64) NOT NULL,
  category_id BIGINT,
  icon        VARCHAR(255),
  price_coin  INT NOT NULL,
  status      ENUM('on','off') NOT NULL DEFAULT 'on',
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_offering_cat FOREIGN KEY (category_id) REFERENCES offering_category(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE cemetery (
  id             BIGINT PRIMARY KEY AUTO_INCREMENT,
  deceased_name  VARCHAR(64) NOT NULL,
  gender         ENUM('male','female') NOT NULL,
  birthday       DATE,
  death_day      DATE,
  epitaph        TEXT,
  creator_user_id BIGINT,
  creator_account VARCHAR(64),
  relation       VARCHAR(32),
  avatar_url     VARCHAR(255),
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_cemetery_user FOREIGN KEY (creator_user_id) REFERENCES user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE sacrifice_order (
  id               BIGINT PRIMARY KEY AUTO_INCREMENT,
  order_no         VARCHAR(64) NOT NULL UNIQUE,
  user_id          BIGINT NOT NULL,
  cemetery_id      BIGINT,
  deceased_name    VARCHAR(64),
  relation         VARCHAR(32),
  offering_id      BIGINT NOT NULL,
  offering_name    VARCHAR(64) NOT NULL,
  offering_category VARCHAR(64),
  price_coin       INT NOT NULL,
  quantity         INT NOT NULL,
  total_coin       INT NOT NULL,
  rmb_amount       DECIMAL(12,2) NOT NULL,
  rate_at_order    DECIMAL(12,4) NOT NULL,
  pay_status       ENUM('unpaid','paid') NOT NULL DEFAULT 'unpaid',
  created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  paid_at          DATETIME,
  CONSTRAINT fk_sorder_user FOREIGN KEY (user_id) REFERENCES user(id),
  CONSTRAINT fk_sorder_cemetery FOREIGN KEY (cemetery_id) REFERENCES cemetery(id),
  CONSTRAINT fk_sorder_offering FOREIGN KEY (offering_id) REFERENCES offering(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE sacrifice_feed (
  id              BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id         BIGINT,
  user_mobile     VARCHAR(20),
  offering_name   VARCHAR(64),
  deceased_name   VARCHAR(64),
  relation        VARCHAR(32),
  content         TEXT,
  sacrifice_time  DATETIME NOT NULL,
  created_by_admin BIGINT,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_sf_user FOREIGN KEY (user_id) REFERENCES user(id),
  CONSTRAINT fk_sf_admin FOREIGN KEY (created_by_admin) REFERENCES admin_user(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========== 6. 内容与教学 ==========

CREATE TABLE article_category (
  id         BIGINT PRIMARY KEY AUTO_INCREMENT,
  name       VARCHAR(64) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE article (
  id           BIGINT PRIMARY KEY AUTO_INCREMENT,
  title        VARCHAR(255) NOT NULL,
  category_id  BIGINT NOT NULL,
  cover_image  VARCHAR(255),
  content_html MEDIUMTEXT,
  status       ENUM('draft','published') NOT NULL DEFAULT 'draft',
  published_at DATETIME,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_article_cat FOREIGN KEY (category_id) REFERENCES article_category(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE teach_video (
  id           BIGINT PRIMARY KEY AUTO_INCREMENT,
  title        VARCHAR(255) NOT NULL,
  cover_image  VARCHAR(255),
  video_url    VARCHAR(255) NOT NULL,
  status       ENUM('on','off') NOT NULL DEFAULT 'on',
  published_at DATETIME,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE courseware (
  id           BIGINT PRIMARY KEY AUTO_INCREMENT,
  title        VARCHAR(255) NOT NULL,
  cover_image  VARCHAR(255),
  file_url     VARCHAR(255) NOT NULL,
  published_at DATETIME,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE one2one_course (
  id             BIGINT PRIMARY KEY AUTO_INCREMENT,
  title          VARCHAR(255) NOT NULL,
  image          VARCHAR(255),
  description_html MEDIUMTEXT,
  expert_id      BIGINT,
  published_at   DATETIME,
  status         ENUM('on','off') NOT NULL DEFAULT 'on',
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE live_event (
  id           BIGINT PRIMARY KEY AUTO_INCREMENT,
  title        VARCHAR(255) NOT NULL,
  live_start   DATETIME NOT NULL,
  live_end     DATETIME,
  live_url     VARCHAR(255) NOT NULL,
  status       ENUM('not_started','living','ended') NOT NULL DEFAULT 'not_started',
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ========== 7. 运营配置与首页 ==========

CREATE TABLE exchange_rate (
  id            BIGINT PRIMARY KEY AUTO_INCREMENT,
  currency      ENUM('bless_coin','memory_coin') NOT NULL,
  rate          DECIMAL(12,4) NOT NULL,
  effective_from DATETIME,
  effective_to   DATETIME,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE pay_qr (
  id         BIGINT PRIMARY KEY AUTO_INCREMENT,
  pay_method ENUM('wechat','alipay') NOT NULL,
  image_url  VARCHAR(255) NOT NULL,
  remark     VARCHAR(255),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE expert_contact (
  id          BIGINT PRIMARY KEY AUTO_INCREMENT,
  name        VARCHAR(64) NOT NULL,
  title       VARCHAR(128),
  avatar_url  VARCHAR(255),
  mobile      VARCHAR(20),
  wechat      VARCHAR(64),
  description VARCHAR(255),
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE home_banner (
  id          BIGINT PRIMARY KEY AUTO_INCREMENT,
  image_url   VARCHAR(255) NOT NULL,
  link_type   ENUM('product','article','external') NOT NULL,
  link_target BIGINT,
  link_url    VARCHAR(255),
  sort_order  INT NOT NULL DEFAULT 0,
  online      TINYINT NOT NULL DEFAULT 1,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE home_section (
  id         BIGINT PRIMARY KEY AUTO_INCREMENT,
  key_name   VARCHAR(64) NOT NULL,
  title      VARCHAR(64) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE home_section_product (
  section_id BIGINT NOT NULL,
  product_id BIGINT NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  PRIMARY KEY (section_id, product_id),
  CONSTRAINT fk_hsp_section FOREIGN KEY (section_id) REFERENCES home_section(id),
  CONSTRAINT fk_hsp_product FOREIGN KEY (product_id) REFERENCES product(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

麻雀店「ぱいんりばー」向けの三人麻雀の成績管理アプリ（Streamlit）。データはすべて Google スプレッドシートに保存する。テスト・lint・`requirements.txt` は無い。

**アプリは2本ある。それぞれ独立した Streamlit アプリで、同じスプレッドシートを共有している。**

| ファイル | 役割 | 使う人 |
|---|---|---|
| `main.py` | 閲覧・分析用のメインアプリ（約9,000行）。成績の入力機能は持たない | お客さん・スタッフ |
| `ranking_view.py` | 成績入力＋着順表の専用アプリ（約1,400行） | 入力担当スタッフ |

ファイル名は GitHub (`f09c0528tgs/mahjong-score-app`、ブランチ `main`) と同じ。このフォルダの `origin` がそのリポジトリで、push すると公開中のアプリにすぐ反映される可能性がある。依存パッケージは `requirements.txt`。

どちらかを直すときは、もう一方に同じロジック（`EXPECTED_COLS`、論理日付、タイプ判定など）が重複していないか必ず確認すること。

## 実行

```bash
pip install streamlit pandas altair st-gsheets-connection

streamlit run main.py           # メインアプリ
streamlit run ranking_view.py      # 入力アプリ
```

Google スプレッドシートへの接続設定は `.streamlit/secrets.toml` の `[connections.gsheets]` に書く（`st.connection("gsheets", type=GSheetsConnection)` が参照する）。リポジトリには入っていないので、無いと読み込みに失敗する。

**デザインは2本とも「平らなキー」**（温かいベージュの背景・フラットな白いキー・こげ茶のアクセント。2026-11-20〜）。`.streamlit/config.toml` は両アプリ共通のライトテーマ（背景 `#e9e4e2`、文字 `#2b2422`、アクセント `#6e5236`）。どちらのアプリも、部品の色はテーマに関係なく CSS でも固定している（config が効かない環境でも同じ見た目になるように）。

- 文字と背景のコントラスト比は 4.5 以上を目安にする。明るい背景では、以前の金色 `#f0c040` のような明るいアクセントは読めない（約1.6）。アクセント色はメインアプリの `:root`（`--accent #6e5236` / `--green #24633f` / `--red #9a2f2f` / `--blue #274f85` など）の濃さ以上にすること。
- 色付きの背景（こげ茶のボタン・バッジ等）の上の文字は白。メダル色（`.preview-rank`）と紙の着順表（`.paper-table`）の色は別扱い。

## 共有データ（ワークシート）

| 定数 | シート | 中身 |
|---|---|---|
| `SHEET_SCORE` | `score` | 1行が1対局。列は `EXPECTED_COLS`（GameNo, TableNo, SetNo, 日時, 備考, A/B/C の さん・タイプ・着順） |
| `SHEET_MEMBER` | `members` | 名前, 登録日, タイプ, 最大飜数, 最大飜数詳細, 最大飜数記録日, 役満回数 |
| `SHEET_LOG` | `logs` | 日時, 操作（新規登録/修正/削除）, GameNo, 詳細 |
| `SHEET_PROFIT` | `daily_profits` | Date, TimeSlot（Day/Night）, MixDiff, RealProfit |
| `SHEET_PENDING` | `pending_buffer` | 仮保存（まとめて保存前）の対局データ |
| `SHEET_RATING` | `ratings` | 名前, レート, 対局数, 段位Index, 段位pt |
| `SHEET_PLAYER_PROFIT` | `player_profits` | 名前, 年月, 収支pt, 備考（手入力。`PLAYER_PROFIT_COLS`） |
| `SHEET_FEE`（入力アプリのみ） | `fee_collections` | ゲーム代の集金記録＝着順表の区切り。日時, TableNo, LastGameNo, 枚数, 内訳（`FEE_COLS`）。無ければ初回の集金時に自動作成 |

- **入力アプリは `st.connection` を使わず gspread を直接使う**（速度のため。同じ secrets を読む）。表示用は `_fetch_all()` で score / members / fee_collections を `values_batch_get` の1回の通信でまとめて読む（60秒キャッシュ）。成績の保存は `append_row` で**末尾に1行追記**（GameNo は保存直前に GameNo 列だけ読んで最大値+1）。集金の取り消しは該当1行を `delete_rows`。シートが無いときの gspread の `WorksheetNotFound` は**メッセージがシート名だけ**なので、型で判定すること（`_is_sheet_missing()`）。以下の「上書き保存」「キャッシュクリア→fresh 読み込み」の話はメインアプリのもの。
- 注意: メインアプリの修正・削除はシート全体を上書きするので、その数秒の間に入力アプリが追記した行は消える可能性がある（以前から同じ）。
- 保存は追記ではない（メインアプリ）。`conn.update()` でシート全体を DataFrame ごと上書きする。
- 読み込みは2種類ある。表示用の `fetch_data_cached` と、保存直前に使う `fetch_data_fresh`（`st.connection`、失敗時は最大3回リトライ）。
  - メインアプリの表示用読み込みも gspread を直接使う。`_BATCH_SHEETS`（score / members / pending_buffer / player_profits / daily_profits）を `_batch_fetch()` で「シート一覧1回＋`values_batch_get` 1回」で読み、`_read_store()`（`st.cache_resource`、全セッション共通）に60秒置く。`process_score_df()` の結果も同じ読み込み結果に対しては使い回す（`_load_score_processed_fast()`）。
  - 値の変換（`_values_to_df()`）は `st.connection` が内部で使う `gspread_dataframe.get_as_dataframe` と同じにしてある。**シートのグリッドの行数・列数まで空欄で埋めるところも含めて同じにすること**（空行があると数値列が float になるなど、型が変わる）。
  - サービスアカウント以外の設定・通信エラーのときは、従来の `conn.read`（`_fetch_single_cached`）に自動で戻る。
  - キャッシュを捨てるのは今までどおり `fetch_data_cached.clear()`（`_fetch_pending_cached.clear()` / `_fetch_player_profit.clear()` も同じ処理）。書き込み処理は必ず「キャッシュをクリア → `load_score_data_fresh()` で最新を取得 → 変更を加える → `save_score_data()`」の順で行う。複数端末から同時に入力されても上書きで消えないようにするためなので、この流れは崩さないこと。
- `save_score_data()` は `EXPECTED_COLS` の列だけを保存する。`process_score_df()` が付け足す派生列（`日時Obj`, `論理日付`, `DailyNo`）は保存されない。シートに列を追加するときは `EXPECTED_COLS` も更新する。
- `GameNo` は内部用の通し番号（最大値+1）。画面に出す「No.」は `DailyNo`（論理日付×卓ごとの連番）。

## 共通ルール

### 日付と時間帯
- 営業日（`論理日付`）は朝9時で切り替わる。`論理日付 = 日時 - 9時間` の日付。
- 時間帯は「昼の部 9:00-21:00」と「夜の部 21:00-翌9:00」の2つだけ。
- 時刻はすべて JST（`timezone(timedelta(hours=9))`）で扱う。

### プレイヤーのタイプ
- `A客` / `B客` / `AS` / `BS` の4種。末尾が `s`/`S` の名前はスタッフ扱い（`_is_staff_name()`）。
- 表記ゆれは `_normalize_play_type()` で吸収する。
- **ゲーム代**: トップを取った人が払う。枚数は `GAME_FEE_TABLE`（A客3枚 / B客4枚 / AS1枚 / BS1枚）。打数ではなくトップ回数に掛けること。

### ランキング集計の決まりごと
- 同率スコアは**同率順位**にする。`assign_competition_rank(df, sort_col, ascending)` を使う（1224式）。
- 「5連勝以上回数」のような**カウント系はスコア0の人を対象外**にする。
- **連続記録（最長連勝・最長連続ラス回避など）は単日のみ**。日付をまたいだ連続はカウントしない。
  - 連続記録は**プレイヤーごと**に「日時 → GameNo」の順で並べて数え、**論理日付が変わったらリセット**する。卓をまたいで交互に入力されても、ほかの卓の局は間に入らない（2026-11 にテストデータで確認済み: 3卓同時・途中で卓を移動・0時またぎ・9時またぎ・後から日時指定で入力）。個人ページ（`page_personal` の `_max_streak` / `_current_streak` / `_after_rate`）も同じルール。
- ランキングPT: 各項目で 1位10pt / 2位7pt / 3位5pt / 4位3pt / 5位2pt / 6〜10位1pt。集計対象は10項目から「レーティング」「段位」を除いた構成。

### レーティングと段位
- レーティングは `RATING_INIT = 1500` スタート。基本ポイントは 1着 `+30` / 2着 `-10` / 3着 `-17`。
- 調整係数は `_rating_adjust_factor(games)`。350戦以降は一律 `0.3`。
- 相手レートとの差による補正は `(opp_avg - cur) / 40.0` で、`RATING_CORRECTION_CAP = 5.0` で±5ptに丸める。**この丸め処理はコード中2か所にあるので、片方だけ直さないこと。**
- 段位は**累積pt方式**（リセット無し）。`DAN_TABLE` の閾値と `DAN_POINTS_1/2/3`（+30 / -3 / -15）で決まる。
- 調整の目安: **2000戦で平均着順1.95を切る人が八段以上になること**。定数を触ったらこの基準で確認する。

## メインアプリ `main.py`

ファイルは番号付きのセクションに分かれている：CSS → データ管理関数 → レーティング/段位 → 共通 UI → 各 `page_*()` → メインルーティング。

### ページ遷移
- Streamlit の multipage 機能は使っていない。`st.session_state["page"]` に文字列を入れて `st.rerun()` し、ファイル末尾の if/elif で `page_*()` を呼び分ける。
- ページを追加するときは `NAV_ITEMS`、末尾のルーティング、そしてそのページの先頭で呼ぶ `render_top_nav("<key>")` の3か所を揃える。
- 現在のページ: `home` / `personal` / `history` / `versus2` / `versus3` / `edit` / `ranking` / `monthly` / `sheets` / `profitpt`。
- ページをまたいで値を渡すときも session_state を使う（`personal_player` / `jump_to_player` / `editing_game_id` / `success_msg` など）。

### 計算の速さ
- **重い集計は `@_memo_by_data` で結果を使い回している**（`get_all_member_names` / `load_ratings_effective` / `get_player_rating_history` / `get_player_top5_rankings` / `compute_ranking_points_all` / `compute_period_basic_stats`）。キーは「引数＋元データ（成績・メンバー・仮保存）の指紋（`_data_key()`）」なので、データが1件でも変われば計算し直しになる。全セッション共通で、返り値は複製して返す。
  - 付けてよいのは「成績・メンバー・仮保存だけから結果が決まり、画面に何も描かない」関数だけ。今日の日付・`session_state`・他のシートを見る関数や、`st.*` で描画する関数に付けると、古い結果が出たり表示が消えたりする。
  - 消すときは `<関数>.clear()`（全部の使い回しが消える）。
- **行のループは `df.iterrows()` ではなく `_rows(df)` を使う**（行は dict。`row["列名"]` / `row.get()` で読む）。iterrows は数千行で遅い。数値列だけの表では iterrows と同じ結果にするため自動で iterrows に戻る。
- 「1行=1対局」を「1行=1人の1対局」（name / rank / date / dt / game_no / player_type / seat）に展開するのは `_build_score_records(df)`。ランキング系の集計はこれを使う。

### UI の注意点
- カード類は `st.markdown(..., unsafe_allow_html=True)` で HTML を直接組み立てている。
- **HTML を `st.markdown` に渡すときは必ず `_html()` を通すこと。** 行頭に4つ以上の空白が入った HTML は Markdown にコードブロックと解釈され、タグがそのまま画面に出る。`_html()` は改行とインデントを除去する。過去に役満回数タブでこのバグが出ている。
- グラフは Altair。背景・目盛りの色は `configure_view(fill="#f1edec")` / `configure_axis(gridColor="#e2dbd6", labelColor="#5a504a")` に合わせる（暗い色を戻さないこと）。
- 配色の上書きは `hide_style` の末尾「デザイン統一 (2026-11-20)」にまとめてある（ボタン・タブ・入力欄・プルダウン・お知らせ枠・`st.metric` など）。ボタンの CSS は `.stButton button`（子孫）で書く。`st.form_submit_button` は `.stButton` ではなく `[data-testid="stFormSubmitButton"]` なので別に指定している。
- **`st.markdown('<div class="...">')` で Streamlit の部品を囲むことはできない**（div はその場で閉じられ、部品は外に出る。空の要素ができて余白だけ増える）。部品に CSS を当てたいときは `st.container(key="...")` で囲み、Streamlit が付ける `st-key-<key>` クラスを目印にする（上部ナビ `st-key-topnav`、ホームのメニュー `st-key-home_menu` / `st-key-menu-<色>-<ページ>`）。
- Streamlit 1.5x では `.main .block-container` が効かない。ページ全体の余白は `[data-testid="stMainBlockContainer"]` に当てる。
- スマホ (幅640px以下) 向けの調整は CSS 末尾の「UI改善 (2026-11)」にまとめてある: 上部ナビは横1列で横スクロール、ホームのメニューは2列、`st.metric` を並べた列は2列、`.stats-table` は文字単位で折り返さず横スクロール。タッチ端末で押した後もボタンが光ったままになる (hover が残る) のは `@media (hover: none)` で消している。
- 利益管理ページの保存パスワード（`"7777"`）がコードに直接書かれている。

## 入力アプリ `ranking_view.py`

手書きの着順表を模した3タブ構成（`main()` 内の `st.tabs`）：

1. **成績を付ける** (`page_input`) — 卓・セット・3人の名前/タイプ/着順を入力して `append_score_row()` で追記
2. **今日の着順表** (`page_today`) — `get_today_logical_date()` の対局を紙の表そっくりに表示
3. **過去の着順表** (`page_past`) — 日付を選んで同じ表を表示

- `render_paper_sheet()` / `_render_table()` が表の描画。**メンバーが入れ替わったら名前の行を再挿入する**実装になっている。座席ごとに `mode()` で代表者を決める実装に戻すと、代走が入ったときに名前が消えるので戻さないこと。
- 名前を選ぶとタイプが自動で選ばれる（`resolve_player_type()`）。優先順は `members` シートのタイプ → その人の前回の対局のタイプ（`get_last_played_types()`）→ 名前から推測（`_guess_type_from_name()`）。画面の表示名は A客 / B客 / Aスタッフ / Bスタッフ だが、保存する値は `A客`/`B客`/`AS`/`BS` のまま。
- 入力アプリにも `_normalize_play_type()` があり、メインアプリの同名関数と同じルール。片方を直したらもう片方も直すこと。
- **ゲーム代を集める**（`render_fee_collect_section()` → `collect_game_fee()`）: 押すと `fee_collections` に1行追記し、着順表がそこで区切られる。区切りは**卓ごと**で、「前回の集金の次の局〜今回の `LastGameNo`」が1区切り（`get_fee_cuts()` / `_render_table()` の `_sec`）。区切りごとにトップ回数×`GAME_FEE_TABLE` で枚数と内訳を出す（`calc_game_fee()`）。表示は毎回対局データから計算し直し、シートの「枚数」「内訳」は記録用。`GAME_FEE_TABLE` はメインアプリと同じ値を重複して持っているので、変えるときは両方直すこと。
- **デザイン (2026-11-20〜)**: 「平らなキー」— 温かいベージュの背景・フラットな白いキー・こげ茶のアクセント（`CUSTOM_CSS` 先頭の `:root` の色）。config.toml はメインアプリと共通（ライト）だが、**画面に出る部品の色はテーマに関係なくすべて CSS で固定**している（入力欄・プルダウンの候補一覧・カレンダー・お知らせ枠・折りたたみなど）。ライトテーマでもダークテーマでも読めることを確認すること。
- **文字色**: 文字と背景のコントラスト比 4.5 以上を目安にする。タブの背景切り替えアニメーションは一瞬読めなくなるので切ってある。
- **成績を付ける画面の構成**: 上のカード（卓・セット・何局目・未集金）と選手チップ（`_chips_html()`、着順が決まるとトップをこげ茶で強調）は、`st.empty()` で場所だけ取っておき、名前・着順が決まったあと最後に中身を描く。
- **操作ボタンは画面の下に固定**（`st.container(key="action_bar")`、[クリア][保存して次へ][保存して空席に]）。Streamlit は `st.container` を同じ高さの `stLayoutWrapper` で包むので、`position: sticky` はその外側（`[data-testid="stLayoutWrapper"]:has(> .st-key-action_bar)`）に付けている。中の要素に付けても固定されない。
- **ボタンの CSS は `.stButton button`（子孫）で書く**。`help=` を付けたボタンは間にツールチップ用の要素が入るので、`.stButton > button` だと当たらない。
- **押しやすさ**: タイプ・着順のボタン (`st.segmented_control`) は、離れた平らなキーとして横幅いっぱいに並べている（着順は `st.container(key="rank_area")` 内で高さ64px）。Streamlit はボタン群の内側の div に `max-width: fit-content` を付けるので、`[data-testid="stButtonGroup"] > div` の `max-width: none` を消すと幅いっぱいにならない。セット、下の操作ボタン、集金の確認ボタンはスマホでも横並び（`.st-key-table_set` / `.st-key-action_bar` / `.st-key-fee_confirm`）。
- **2卓以上**: 卓は上の切り替えボタン（`st.container(key="table_pick_area")`、今日立っている卓＋「＋次の卓」）で選ぶ。卓ごとに色と印（`TABLE_MARKS` / `TABLE_COLORS`）を決めてあり、上のカード・下の「入力先」・着順表の見出しで同じ色を使う。**名前・セット・手で変えたタイプは卓ごとに覚える**（名前欄のキーは `sel_name_<卓>_<席>`、控えは `_table_mem()`）。Streamlit は画面に出ていない入力欄の値を捨てるので、別の卓から戻ったときは控えから戻している。選んだ人がほかの卓の最後の局（`get_table_status()`）や、ほかの卓の入力欄にもいると警告を出す（保存は止めない）。
- 卓番が同じ日時の局は GameNo（入力順）で並べる。着順表も区切り→セット→日時→GameNo の順。
- 入力欄を空に戻すときは、session_state のキーを `del` しないこと（ブラウザ側に古い値が表示されたまま残る）。ウィジェットを描く前に値を `None` / `""` にセットする（`_clear_seats()` と `input_pending_reset` を参照）。

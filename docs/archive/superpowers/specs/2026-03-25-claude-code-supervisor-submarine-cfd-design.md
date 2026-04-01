# Claude Code Supervisor + DeerFlow 娼滆墖 CFD 鏅鸿兘浣撶郴缁熻璁?
## 1. 鏂囨。鐩殑

杩欎唤鏂囨。瀹氫箟褰撳墠浠撳簱鎺ヤ笅鏉ョ殑鍞竴涓荤嚎锛氬湪 DeerFlow 涔嬩笂鏋勫缓闈㈠悜娼滆墖 CFD 浠诲姟鐨勪笓涓氭櫤鑳戒綋绯荤粺锛屽苟鎶?`Claude Code` 鏀惧湪 DeerFlow 瀹樻柟鎺ㄨ崘鐨勪綅缃笂锛屼綔涓哄灞傛€绘帶鍏ュ彛浣跨敤銆?
瀹冧笉鏄 [2026-03-25-deerflow-replatform-design.md](/C:/Users/D0n9/Desktop/棰犺鎬уぇ璧?docs/archive/superpowers/specs/2026-03-25-deerflow-replatform-design.md) 鐨勬浛浠ｏ紝鑰屾槸璇ラ噸鏋勫喅绛栦箣鍚庣殑姝ｅ紡绯荤粺璁捐銆傚墠涓€浠芥枃妗ｅ洖绛斺€滀负浠€涔堝垏鍒?DeerFlow鈥濓紱杩欎竴浠藉洖绛斺€滃垏杩囧幓涔嬪悗绯荤粺搴旇闀挎垚浠€涔堟牱锛屼互鍙婂浣曞厖鍒嗕娇鐢?DeerFlow 鐨勮兘鍔涒€濄€?
## 2. 鏍稿績鍐崇瓥

褰撳墠绯荤粺閲囩敤涓夊眰缁撴瀯锛?
1. `Claude Code Supervisor`
   璐熻矗鐢ㄦ埛鎰忓浘鐞嗚В銆佹柟妗堢‘璁ゃ€侀樁娈甸棬鎺с€佽川閲忓闃呫€佷笌鐢ㄦ埛鐨勯珮灞備氦浜掋€?2. `DeerFlow CFD Runtime`
   璐熻矗 thread銆乽pload銆乤rtifact銆乵emory銆乻andbox銆乻kills銆丮CP銆乻ubagents 鍜岃繍琛屾€佺紪鎺掋€?3. `涓撲笟鎵ц鑳藉姏灞俙
   璐熻矗鍑犱綍妫€鏌ャ€佹渚嬪尮閰嶃€丱penFOAM 浠诲姟鍑嗗銆佹眰瑙ｈ皟搴︺€佺粨鏋滄暣鐞嗕笌鎶ュ憡鐢熸垚銆?
鍏抽敭绾︽潫濡備笅锛?
- 涓嶅啀鎭㈠鏃х殑杞婚噺鎵ц鍣ㄣ€佹棫璋冨害鍣ㄣ€佹棫鍓嶇涓荤嚎銆?- `legacy/current-prototype/` 鍙綔涓洪鍩熺粡楠屽弬鑰冦€?- 娼滆墖绯荤粺鐨勬牳蹇冧氦浠樼墿鏄彲杩借釜鐨?run銆乤rtifact銆佹姤鍛婂拰缁撴瀯鍖栫粨鏋滐紝鑰屼笉鏄竴娈佃亰澶╁洖澶嶃€?- `Claude Code` 鐨勫畼鏂规帹鑽愭帴鍏ヤ綅鏄?DeerFlow 澶栧眰锛岄€氳繃 `claude-to-deerflow` 涓?DeerFlow HTTP API 浜や簰锛涙湰椤圭洰閬靛惊杩欎釜浣嶇疆銆?
## 3. 鐩爣

绯荤粺搴旀敮鎸佸涓嬩换鍔″舰鎬侊細

1. 鐢ㄦ埛涓婁紶娼滆墖鍑犱綍鏂囦欢锛屼緥濡?`.x_t` 鎴?`.stl`銆?2. 绯荤粺瀹屾垚浠诲姟鐞嗚В銆佹渚嬪尮閰嶃€佸嚑浣曟鏌ャ€佹眰瑙ｅ噯澶囥€佹眰瑙ｈ皟搴︺€佺粨鏋滄暣鐞嗗拰鎶ュ憡鐢熸垚銆?3. 姣忔鎵ц閮藉舰鎴愪竴涓彲灞曠ず銆佸彲杩借釜銆佸彲褰掓。鐨?DeerFlow thread/run銆?4. 鍚庣画鍙互鑷劧鎺ュ叆鐪熷疄 OpenFOAM銆佺湡瀹炰笓涓?skill銆佺湡瀹?MCP 鏈嶅姟鍜岀湡瀹?Claude Code 鍗忎綔閾俱€?
鍚屾椂锛岀郴缁熻鍏呭垎浣跨敤 DeerFlow 鐨勫師鐢熻兘鍔涳紝鑰屼笉鏄彧鎶?DeerFlow 褰撴垚涓€涓亰澶╁３瀛愶細

- `sub-agents`
- `memory`
- `sandbox`
- `skills`
- `MCP`
- `artifacts / threads / uploads`
- `Claude Code integration`

## 4. 闈炵洰鏍?
褰撳墠闃舵涓嶅仛浠ヤ笅浜嬫儏锛?
- 涓嶆仮澶嶆棫鍘熷瀷鎵ц閾捐矾銆?- 涓嶅厛杩芥眰閫氱敤闂瓟 agent銆?- 涓嶅厛鍋氣€滃瑙備紭鍏堚€濈殑鍓嶇缈绘柊銆?- 涓嶅湪 Claude Code 渚у爢涓€濂楀钩琛岀殑鎵ц妗嗘灦銆?- 涓嶆妸 OpenFOAM 鍏堝仛鎴愯劚绂?DeerFlow artifact/thread 浣撶郴鐨勯粦鐩掕剼鏈€?
## 5. 澶囬€夋柟妗堜笌鍙栬垗

### 鏂规 A锛欳laude Code 鍙仛澶栭儴璋冪敤鍣?
Claude Code 鍙礋璐ｅ彂 HTTP 璇锋眰缁?DeerFlow锛孌eerFlow 鍐呴儴浠嶄繚鎸侀€氱敤 lead agent锛屼笉鍋氭繁搴﹂鍩熷寲銆?
浼樼偣锛?
- 鎺ュ叆閫熷害蹇?- 涓庡畼鏂?`claude-to-deerflow` skill 鏈€鎺ヨ繎

缂虹偣锛?
- 娼滆墖棰嗗煙璇箟浼氬仠鐣欏湪澶栧眰
- DeerFlow 鍐呴儴鏃犳硶褰㈡垚绋冲畾鐨勪笓涓氳兘鍔涜竟鐣?- artifact銆乵emory銆乻ubagent 寰堥毦鐪熸鍥寸粫 CFD 宸ヤ綔娴佺粍缁?
### 鏂规 B锛欴eerFlow 鑷繁鎬绘帶锛孋laude 鍙仛妯″瀷鎻愪緵鑰?
鎶?Claude 鍙綋 DeerFlow 鐨勬ā鍨嬶紝鍦?`models` 灞傛帴鍏?`ClaudeChatModel`銆?
浼樼偣锛?
- 鏋舵瀯绠€鍗?- DeerFlow 鍐呴儴缁熶竴

缂虹偣锛?
- 涓嶇鍚堚€淐laude Code 鍋氭€绘帶鈥濈殑鐩爣
- 澶卞幓瀹樻柟 `claude-to-deerflow` 杩欐潯澶栧眰鍗忎綔閾剧殑浠峰€?
### 鏂规 C锛欳laude Code Supervisor + DeerFlow Runtime

Claude Code 鍦ㄥ灞傚仛鎬绘帶涓庤川閲忛棬鎺э紝DeerFlow 鍦ㄥ唴灞傚仛杩愯鏃朵笌涓撲笟鎵ц缂栨帓銆?
浼樼偣锛?
- 鍚屾椂绗﹀悎 DeerFlow 瀹樻柟鎺ㄨ崘鎺ュ叆浣嶅拰椤圭洰褰撳墠璇夋眰
- DeerFlow 鍘熺敓鑳藉姏鍙互瀹屾暣鎵挎帴涓撲笟 run
- Claude Code 璐熻矗涓婂眰娌熼€氥€佸垽鏂笌楠屾敹锛岃亴璐ｆ竻鏅?
缂虹偣锛?
- 闇€瑕佹槑纭?Supervisor 鍜?Runtime 涔嬮棿鐨勫崗璁潰
- 闇€瑕佸 subagent 杈圭晫鍋氭洿涓ユ牸璁捐

鏈」鐩噰鐢ㄦ柟妗?C銆?
## 6. 鎬讳綋鏋舵瀯

### 6.1 Claude Code Supervisor

Supervisor 浣嶄簬 DeerFlow 澶栧眰锛屼紭鍏堥€氳繃 `skills/public/claude-to-deerflow/` 涓?DeerFlow 鐨?Gateway/LangGraph API 浜や簰銆?
鑱岃矗锛?
- 鐞嗚В鐢ㄦ埛浠诲姟涓庣洰鏍囧伐鍐?- 鍋氬繀瑕佺殑婢勬竻鍜屾柟妗堢‘璁?- 鍐冲畾浠€涔堟椂鍊欏惎鍔?DeerFlow run
- 璇诲彇 DeerFlow 杩斿洖鐨?artifact銆佹棩蹇楀拰缁撴瀯鍖栫粨鏋?- 鍋氶樁娈甸棬鎺т笌鏈€缁堣川閲忓垽鏂?- 涓庣敤鎴锋寔缁氦浜?
涓嶈礋璐ｏ細

- 鐩存帴鎵ц OpenFOAM
- 鐩存帴鎵挎媴鍑犱綍瑙ｆ瀽鎴栧悗澶勭悊缁嗚妭
- 鑷繁缁存姢涓€濂楃嫭绔嬬殑 artifact/run 浣撶郴

### 6.2 DeerFlow CFD Runtime

DeerFlow 鏄湡姝ｇ殑杩愯鏃跺唴鏍革紝璐熻矗鎵€鏈変笌鈥滄墽琛屼竴娆′笓涓?CFD 浠诲姟鈥濇湁鍏崇殑鐘舵€佷笌浜х墿绠＄悊銆?
瀹冩壙鎺ワ細

- `thread`
- `upload`
- `artifact`
- `memory`
- `sandbox`
- `skills`
- `MCP`
- `subagents`
- `LangGraph run / stream`

褰撳墠浠撳簱涓殑涓昏鎸傜偣濡備笅锛?
- 涓婁紶鍏ュ彛锛歚backend/app/gateway/routers/uploads.py`
- artifact 鏈嶅姟锛歚backend/app/gateway/routers/artifacts.py`
- 绾跨▼鏁版嵁鐩綍锛歚backend/packages/harness/deerflow/agents/middlewares/thread_data_middleware.py`
- upload 娉ㄥ叆锛歚backend/packages/harness/deerflow/agents/middlewares/uploads_middleware.py`
- skill 娉ㄥ叆锛歚backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
- DeerFlow 鍐呯疆鍑犱綍妫€鏌ュ伐鍏凤細`backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py`
- 娼滆墖杩愯鏃堕鍩熷眰锛歚backend/packages/harness/deerflow/domain/submarine/`

### 6.3 涓撲笟鎵ц鑳藉姏灞?
杩欎竴灞傚洿缁曟綔鑹?CFD 浠诲姟鍋氭媶鍒嗭紝涓嶅啀璧扳€滃崟 agent 澶у寘澶ф徑鈥濈殑璺嚎銆?
绗竴鎵硅鑹茶竟鐣屽畾涔変负锛?
1. `task-intelligence`
   浠诲姟鐞嗚В銆佹渚嬫绱€佹渚嬫帹鑽愩€佹祦绋嬪缓璁€?2. `geometry-preflight`
   鍑犱綍璇嗗埆銆佹牸寮忔鏌ャ€佸昂搴︿及璁°€侀闄╂彁绀恒€佸墠澶勭悊浜х墿鐢熸垚銆?3. `solver-dispatch`
   OpenFOAM case 缁勮銆佹眰瑙ｅ弬鏁版槧灏勩€佹墽琛岃皟搴︺€佽繍琛屾棩蹇椾笌澶辫触鎭㈠銆?4. `result-reporting`
   姹囨€绘棩蹇椼€佸浘琛ㄣ€佹暟鍊肩粨鏋溿€佸舰鎴愪腑鏂囨憳瑕併€佹寮忔姤鍛婁笌 artifact 娓呭崟銆?
杩欎簺杈圭晫宸茬粡鍦?`backend/packages/harness/deerflow/domain/submarine/roles.py` 涓湁浜嗙涓€鐗堝畾涔夛紝鍚庣画闇€瑕佽繘涓€姝ユ紨鍖栦负鐪熸鍙敞鍐岀殑 DeerFlow 涓撲笟 subagents銆?
## 7. DeerFlow 鑳藉姏鏄犲皠

| DeerFlow 鑳藉姏 | 鍦ㄦ綔鑹?CFD 绯荤粺涓殑浣滅敤 |
|---|---|
| `threads` | 姣忎釜娼滆墖浠诲姟瀵瑰簲涓€涓彲杩借釜鐨勫伐浣滅嚎绋嬶紝鎵胯浇涓婁紶銆佹秷鎭€佷骇鐗╁拰鐘舵€?|
| `uploads` | 鎵胯浇 `.x_t`銆乣.stl`銆侀厤缃〃銆佽ˉ鍏呰祫鏂欑瓑杈撳叆 |
| `artifacts` | 鎵胯浇鍑犱綍妫€鏌ョ粨鏋溿€丱penFOAM 鏃ュ織銆佸悗澶勭悊鍥剧墖銆佹渶缁堟姤鍛?|
| `sub-agents` | 鎵胯浇妗堜緥鐞嗚В銆佸嚑浣曢妫€銆佹眰瑙ｈ皟搴︺€佺粨鏋滄暣鐞嗙瓑瑙掕壊鍒嗗伐 |
| `memory` | 淇濈暀妗堜緥缁忛獙銆佺敤鎴峰亸濂姐€佷换鍔′笂涓嬫枃銆佸父瑙佸け璐ユā寮忎笌鏈€浣冲疄璺?|
| `sandbox` | 鎵胯浇鍑犱綍棰勫鐞嗐€丱penFOAM 鏈湴鎴栧鍣ㄥ唴鎵ц銆佸悗澶勭悊鑴氭湰杩愯 |
| `skills` | 鎶婃綔鑹囬鍩熷伐浣滄祦鏄惧紡娉ㄥ叆 lead agent 涓庝笓涓?subagent |
| `MCP` | 鎺ュ叆 CAD/缃戞牸/瀛樺偍/妫€绱?杩滅▼闆嗙兢/鎶ュ憡鏈嶅姟绛夊閮ㄨ兘鍔?|
| `Claude Code integration` | 璁╁灞?Supervisor 瀹樻柟鏂瑰紡鎺ュ叆 DeerFlow锛岃€屼笉鏄嚜閫犲崗璁?|

## 8. 鍏抽敭瀵硅薄妯″瀷

### 8.1 Thread 鍗充换鍔″鍣?
姣忎釜浠诲姟 thread 鑷冲皯瑕佸寘鍚細

- 鐢ㄦ埛杈撳叆娑堟伅
- 涓婁紶鏂囦欢鍒楄〃
- 褰撳墠闃舵鐘舵€?- 涓棿涓庢渶缁?artifact
- 缁撴瀯鍖栫粨鏋滄憳瑕?- 澶辫触鍘熷洜涓庨噸璇曡褰?
杩欐剰鍛崇潃 thread 涓嶆槸鏅€氳亰澶╄褰曪紝鑰屾槸涓€娆℃綔鑹?CFD run 鐨勪富瀹瑰櫒銆?
### 8.2 Artifact 鍗充竴绛夊叕姘?
artifact 闇€瑕佽璁捐鎴愰潰鍚戝睍绀轰笌褰掓。锛岃€屼笉鏄复鏃惰緭鍑烘枃浠躲€傜涓€闃舵鏈€浣庤姹傦細

- `geometry-check.json`
- `geometry-check.md`
- `geometry-check.html`

鍚庣画瑕佹墿灞曚负锛?
- `case-selection.json`
- `solver-plan.md`
- `openfoam-run.log`
- `postprocess-summary.json`
- `report.md`
- `report.html`
- 鍏抽敭鍥剧墖銆佽〃鏍笺€佹洸绾垮浘

### 8.3 Memory 鍗充换鍔＄煡璇嗘矇娣€

Memory 涓嶅簲鍙褰曟硾鐢ㄨ亰澶╀簨瀹烇紝鑰屽簲娌夋穩浠ヤ笅鍐呭锛?
- 甯哥敤娼滆墖鍑犱綍瀹舵棌涓庡搴旀渚?- 甯歌杈撳叆闂涓庝慨澶嶅缓璁?- 鐢ㄦ埛鎴栧洟闃熷亸濂界殑宸ュ喌璁剧疆
- OpenFOAM 姹傝В杩囩▼涓殑甯歌澶辫触妯″紡
- 鎶ュ憡鍙ｅ緞涓庡睍绀哄亸濂?
## 9. End-to-End 杩愯娴?
鏍囧噯浠诲姟娴佸涓嬶細

1. 鐢ㄦ埛鍦?Claude Code 涓彁鍑轰换鍔″苟鎻愪緵杈撳叆銆?2. Claude Code Supervisor 瀹屾垚楂樺眰鎰忓浘鐞嗚В鍜屾柟妗堟緞娓呫€?3. Supervisor 閫氳繃 `claude-to-deerflow` 鍒涘缓 thread锛屽苟涓婁紶鍑犱綍鏂囦欢鍒?DeerFlow銆?4. DeerFlow lead agent 鍔犺浇娼滆墖鎶€鑳斤紝杩涘叆 `submarine-orchestrator` 宸ヤ綔娴併€?5. `task-intelligence` 瀹屾垚妗堜緥鍖归厤涓庢祦绋嬪缓璁€?6. `geometry-preflight` 鎵ц `.x_t` / `.stl` 妫€鏌ュ苟鍐欏叆 artifact銆?7. 鑻ユ鏌ラ€氳繃锛宍solver-dispatch` 缁勮 OpenFOAM case 骞堕€氳繃 sandbox / MCP 鎵ц銆?8. `result-reporting` 姹囨€荤粨鏋溿€佷骇鐗╀笌鎶ュ憡銆?9. DeerFlow thread 杩斿洖鍙睍绀?artifact銆佺粨鏋勫寲缁撴灉鍜屼腑鏂囨憳瑕併€?10. Claude Code Supervisor 璇诲彇缁撴灉锛岃繘琛岃川閲忓鏌ワ紝骞跺悜鐢ㄦ埛姹囨姤銆?
## 10. OpenFOAM 鎺ュ叆鍘熷垯

OpenFOAM 涓嶅簲璇ヤ綔涓轰竴鏉℃父绂诲湪绯荤粺澶栭儴鐨勮剼鏈摼锛岃€屽簲浣滀负 DeerFlow 杩愯鏃朵腑鐨勫彈鎺ф墽琛岃兘鍔涙帴鍏ャ€?
鎺ㄨ崘鎺ユ硶锛?
1. DeerFlow `solver-dispatch` 璐熻矗鎶婃綔鑹囦换鍔℃槧灏勪负鍙楁帶鐨?OpenFOAM 鎵ц璁″垝銆?2. 鎵ц璁″垝鍦?DeerFlow sandbox 涓惤鍦帮紝鎴栭€氳繃 DeerFlow MCP 杞彂鍒拌繙绔绠楄祫婧愩€?3. 鎵€鏈夋墽琛屾棩蹇椼€侀厤缃€佽緭鍏ユ槧灏勫拰杈撳嚭缁撴灉閮藉洖鍐欏埌 thread artifact銆?4. Claude Code Supervisor 姘歌繙涓嶇洿鎺ユ搷浣?OpenFOAM 鐩綍锛岃€屾槸鍙湅 DeerFlow 杩斿洖鐨勭粨鏋勫寲鐘舵€佷笌浜х墿銆?
杩欎繚璇佷簡锛?
- OpenFOAM 琚撼鍏ョ粺涓€杩愯鏃舵不鐞?- 澶辫触鍙互杩借釜
- 缁撴灉鍙互褰掓。
- 鍚庣画鍙互浠庢湰鍦版墽琛屽垏鍒板鍣ㄦ墽琛屾垨杩滅▼闆嗙兢锛岃€屼笉鏀?Supervisor 渚ф帴鍙?
## 11. 鎶€鑳戒笌 Subagent 璁捐鍘熷垯

娼滆墖绯荤粺涓嶈兘鍙潬涓€涓€氱敤 prompt銆傞鍩熻兘鍔涘繀椤诲浐鍖栦负 DeerFlow 鍙銆佸彲缁勫悎銆佸彲鏇挎崲鐨?skill 涓?subagent 缁撴瀯銆?
鎺ㄨ崘淇濈暀骞舵墿灞曚互涓?skill锛?
- `submarine-orchestrator`
- `submarine-case-search`
- `submarine-geometry-check`
- `submarine-report`
- `submarine-solver-dispatch`
- `submarine-postprocess`

鍏朵腑锛?
- `skills/public/submarine-*` 璐熻矗鎻愮ず涓庡伐浣滄祦绾︽潫
- `backend/packages/harness/deerflow/domain/submarine/*` 璐熻矗缁撴瀯鍖栭鍩熼€昏緫
- 涓撲笟 subagent 閰嶇疆璐熻矗鏄庣‘鎵ц杈圭晫涓庡伐鍏锋潈闄?
## 12. MCP 涓庡閮ㄨ兘鍔涙墿灞?
涓轰簡鐪熸鈥滃厖鍒嗗埄鐢?DeerFlow鈥濓紝MCP 闇€瑕佹垚涓烘綔鑹囩郴缁熺殑闀挎湡鏍囧噯鎵╁睍浣嶏紝鑰屼笉鏄彲鏈夊彲鏃犵殑琛ュ厖銆?
浼樺厛鑰冭檻鐨?MCP 绫诲瀷锛?
- 杩滅▼ OpenFOAM 鎴?HPC 浣滀笟鎻愪氦
- CAD/鍑犱綍妫€鏌ユ湇鍔?- 缃戞牸鐢熸垚鎴栬川閲忚瘎浼版湇鍔?- 瀵硅薄瀛樺偍涓庣粨鏋滃綊妗?- 涓撲笟鐭ヨ瘑搴撲笌妗堜緥妫€绱?- 鎶ュ憡瀵煎嚭涓庝紒涓氬唴閮ㄥ垎鍙?
鍘熷垯鏄細

- DeerFlow 閫氳繃 MCP 鎺ュ叆澶栭儴鑳藉姏
- Claude Code Supervisor 涓嶇洿鎺ョ粫寮€ DeerFlow 璋冭繖浜涙湇鍔?- 鎵€鏈夊閮ㄨ兘鍔涜皟鐢ㄧ粨鏋滄渶缁堝洖鍒?DeerFlow thread/artifact

## 13. 褰撳墠鏂囨。娓呯悊鍐崇瓥

涓洪伩鍏嶇户缁杩佺Щ鏈熸畫鐣欐枃妗ｈ瀵硷紝浠ヤ笅鏂囨。鍦ㄦ湰杞竻鐞嗕腑绉婚櫎锛?
- `docs/CODE_CHANGE_SUMMARY_BY_FILE.md`
- `docs/SKILL_NAME_CONFLICT_FIX.md`
- `docs/archive/superpowers/plans/2026-03-25-submarine-deerflow-minimum-loop.md`

娓呯悊鍘熷洜锛?
- 瀹冧滑灞炰簬涓存椂杩佺Щ璇存槑鎴栧凡缁忚鏂颁富绾胯鐩?- 涓嶈兘浣滀负褰撳墠鏋舵瀯鍐崇瓥渚濇嵁
- 浼氭妸娉ㄦ剰鍔涙媺鍥炴棫闂鎴栫獎鑼冨洿闃舵鎬ф柟妗?
## 14. 鍒嗛樁娈靛疄鏂藉缓璁?
### Phase 1锛歋upervisor/Runtime 濂戠害瀹氬瀷

- 鏄庣‘ Claude Code Supervisor 璋冪敤 DeerFlow 鐨勪换鍔″崗璁?- 缁熶竴 thread銆乽pload銆乤rtifact 鐨?run 璇箟
- 淇濇寔宸叉湁鍑犱綍妫€鏌ユ渶灏忛棴鐜彲鐢?
### Phase 2锛氫笓涓?Subagent 缁撴瀯钀藉湴

- 鎶?`roles.py` 涓殑瑙掕壊杈圭晫鍙樻垚鐪熸鍙皟鐢ㄧ殑 DeerFlow 涓撲笟 subagents
- 璁?`submarine-orchestrator` 浼樺厛璋冨害涓撲笟 subagents锛岃€屼笉鏄彧渚濊禆閫氱敤浠ｇ悊

### Phase 3锛歄penFOAM 鍙楁帶鎺ュ叆

- 瀹氫箟 `solver-dispatch` 鐨勮緭鍏ヨ緭鍑哄绾?- 鍦?sandbox 鎴?MCP 涓婃帴鍏ョ湡瀹?OpenFOAM 杩愯閾?- 璁╂棩蹇椼€侀厤缃拰缁撴灉閮借繘鍏?artifact

### Phase 4锛氱粨鏋滀笌鎶ュ憡浜у搧鍖?
- 瀹屾垚缁撴灉姹囨€汇€佷腑鏂囨姤鍛娿€佸浘琛ㄤ笌缁撴灉闈㈡澘
- 璁?DeerFlow 鍓嶇閫愭婕斿寲鎴愭綔鑹囦豢鐪熷伐浣滃彴

## 15. 鎴愬姛鏍囧噯

婊¤冻浠ヤ笅鏉′欢鏃讹紝鍙涓虹郴缁熻繘鍏ユ纭富绾匡細

1. Claude Code 璐熻矗楂樺眰鎬绘帶锛屼絾涓嶇洿鎺ユ壙鎷呭簳灞傛墽琛屻€?2. DeerFlow 鎴愪负鍞竴杩愯鏃跺唴鏍革紝瀹屾暣鎵胯浇 thread銆乽pload銆乤rtifact銆乵emory銆乻andbox銆乻kills銆丮CP 鍜?subagents銆?3. 娼滆墖浠诲姟鍙互褰㈡垚浠庝笂浼犲埌缁撴灉鎶ュ憡鐨勫畬鏁?run銆?4. OpenFOAM銆佷笓涓氭湇鍔″拰鍚庣画鍥㈤槦鍗忎綔鑳藉姏閮借兘鍦?DeerFlow 浣撶郴鍐呰嚜鐒舵帴鍏ャ€?5. 浠撳簱涓笉鍐嶄繚鐣欎細璁╁紑鍙戣€呰鍒や富绾跨殑鏃ц鍒掓垨杩佺Щ娈嬬暀鏂囨。銆?
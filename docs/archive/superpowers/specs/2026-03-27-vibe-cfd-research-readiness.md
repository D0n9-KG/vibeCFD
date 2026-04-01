# 闈㈠悜绉戠爺宸ヤ綔鐨?Vibe CFD 宸窛銆佸閮ㄨˉ褰曡姹備笌浠撳簱鎺ㄨ繘璁板綍

## 1. 鏂囨。鐩殑

杩欎唤鏂囨。鏈嶅姟浜庡綋鍓?DeerFlow 涓荤嚎涓嬬殑 `vibe CFD` 椤圭洰锛岀洰鏍囦笉鏄啀璁ㄨ鏄惁鍥炲埌鏃у師鍨嬶紝鑰屾槸鍥炵瓟涓変釜鏇村疄闄呯殑闂锛?
1. 瑕佹妸褰撳墠绯荤粺鎺ㄨ繘鍒扳€滅湡姝ｅ彲鐢ㄤ簬绉戠爺宸ヤ綔鈥濈殑绾у埆锛岃繕缂轰粈涔堛€?2. 杩欎簺缂哄彛閲岋紝鍝簺蹇呴』鐢变粨搴撳閮ㄨˉ褰曪紝琛ュ綍鍐呭瑕佸叿浣撳埌浠€涔堢矑搴︺€?3. 鍦ㄤ笉绛夊緟鍏ㄩ儴澶栭儴鏉′欢灏辩华鐨勫墠鎻愪笅锛屽綋鍓嶄粨搴撳唴杩樿兘缁х画鎺ㄨ繘鍝簺鑳藉姏锛屼互鍙婂綋鍓嶇湡瀹炵姸鎬佹槸浠€涔堛€?
鏈枃妗ｅ埢鎰忓厛鍐欏閮ㄥ繀椤昏ˉ褰曠殑鍐呭锛屽洜涓鸿繖鍐冲畾浜嗕粨搴撳唴寰堝鑳藉姏鐨勪笂闄愩€傛病鏈?benchmark銆佷笓涓氶獙鏀惰鍒欏拰棰嗗煙涓撳鍏卞垱鍐呭锛岀郴缁熸渶澶氬彧鑳藉仛鍒扳€滅粨鏋勫寲銆佸彲杩借釜銆佸彲灞曠ず鈥濓紝杩樺仛涓嶅埌鈥滃彲浠ユ敮鎾戠鐮斿垽鏂€濄€?
## 2. 澶栭儴蹇呴』琛ュ綍鐨勫唴瀹逛笌鍏蜂綋瑕佹眰

### 2.1 CFD 鍩哄噯妗堜緥涓庨獙鏀惰鍒欏寘

杩欐槸鏈€鍏抽敭鐨勫閮ㄨˉ褰曢」銆傚綋鍓嶄粨搴撳凡缁忔湁 `domain/submarine/cases/index.json` 閲岀殑妗堜緥搴擄紝浣嗗畠鏇村儚 workflow template锛屼笉鏄鐮旈獙鏀舵暟鎹寘銆傜湡姝ｉ潰鍚戠鐮斿伐浣滐紝鑷冲皯瑕佷负姣忎釜涓荤敤妗堜緥琛ュ叆浠ヤ笅淇℃伅锛?
- 妗堜緥韬唤锛?  - 鏍囧噯妗堜緥鍚嶇О
  - 妗堜緥鏉ユ簮鏂囩尞鎴栧叕寮€鎶ュ憡
  - 鍑犱綍鐗堟湰璇存槑
  - 宸ュ喌閫傜敤鑼冨洿
- 鍙傝€冪湡鍊兼垨瀹瑰樊锛?  - `Cd / Cl / Cm` 鐨勫弬鑰冨€笺€佸弬鑰冨尯闂存垨瀹硅璇樊
  - 鍘嬪姏鍒嗗竷銆佸熬杩归€熷害浜忔崯銆佸吀鍨嬫埅闈㈡暟鎹?  - 鍏佽閲囩敤鐨勬瘮杈冩柟寮忥紝鏄偣鍊笺€佹洸绾胯秼鍔胯繕鏄尯闂村垽瀹?- 璁＄畻鍙俊搴﹂棬妲涳細
  - 鏈€澶у彲鎺ュ彈娈嬪樊
  - 鏈€灏戞眰瑙ｆ椂闂存垨鏀舵暃鍒ゆ嵁
  - 缃戞牸璐ㄩ噺鍜岀綉鏍肩嫭绔嬫€ф渶灏忚姹?  - 鍩熷昂瀵搞€佽竟鐣屾潯浠躲€佹箥娴佹ā鍨嬬害鏉?- 鎶ュ憡蹇呬氦椤癸細
  - 蹇呴』鍑虹幇鐨勫浘琛?  - 蹇呴』鍑虹幇鐨勫姣旇〃
  - 蹇呴』璁板綍鐨勬眰瑙ｅ弬鏁?  - 蹇呴』褰掓。鐨勪腑闂?artifacts

鍏蜂綋瑕佹眰锛?
- 姣忎釜閲嶇偣妗堜緥閮藉簲褰㈡垚缁撴瀯鍖?JSON/YAML锛岃€屼笉鏄彧缁欎竴娈垫枃瀛楄鏄庛€?- 姣忔潯楠屾敹瑙勫垯閮借鏄庣‘锛?  - 鏁版嵁鏉ユ簮
  - 閫傜敤鏉′欢
  - 闃堝€兼垨姣旇緝鏂规硶
  - 涓嶆弧瓒虫椂搴斿垽瀹氫负 `warning` 杩樻槸 `blocked`
- 绗竴鎵硅嚦灏戝簲瑕嗙洊锛?  - `DARPA SUBOFF bare hull resistance`
  - `DARPA SUBOFF pressure distribution`
  - `Joubert BB2 wake / pressure`
  - `Type 209 engineering drag`

濡傛灉杩欎竴鍖呬笉琛ラ綈锛岀郴缁熷彧鑳藉仛鈥滅粨鏋滄暣鐞嗏€濆拰鈥滃伐绋嬪惎鍙戝紡鎻愮ず鈥濓紝涓嶈兘鍋氣€滅鐮旈獙鏀垛€濄€?
### 2.2 涓撲笟 CFD Skills 鍐呭鍖?
褰撳墠浠撳簱鍐呭凡缁忔湁 DeerFlow 鎶€鑳戒綋绯汇€丼kill Studio銆乬raph銆乸ublish/install 娴佺▼锛屼絾鈥滅鐮斿彲鐢ㄢ€濈殑闅剧偣鍦?skill 鍐呭锛岃€屼笉鏄?skill 澶栧３銆?
澶栭儴闇€瑕佽ˉ褰曠殑 skill 鍐呭鑷冲皯鍖呮嫭锛?
- 鍑犱綍棰勬 skill锛?  - STL 鎷撴墤/灏哄害/闂悎鎬ф鏌ヨ鍒?  - 娼滆墖鍑犱綍鏃忚瘑鍒粡楠?  - 甯歌闂鍒嗙被涓庡鐞嗗缓璁?- 缃戞牸鍑嗗 skill锛?  - 涓嶅悓浠诲姟绫诲瀷鐨勭綉鏍肩瓥鐣?  - 灞€閮ㄥ姞瀵嗗缓璁?  - 澹侀潰澶勭悊銆佽竟鐣屽眰灞傛暟銆侀灞傞珮搴﹀缓璁?- OpenFOAM 姹傝В skill锛?  - 姹傝В鍣ㄩ€夋嫨瑙勫垯
  - 婀嶆祦妯″瀷閫夋嫨瑙勫垯
  - 绋虫€?鐬€佸垏鎹㈡潯浠?  - 鎺у埗鍙傛暟榛樿鍊煎拰璋冩暣绛栫暐
- 鍚庡鐞?skill锛?  - 鍔涚郴鏁版彁鍙?  - 鍘嬪姏鍥俱€佹祦绾裤€佸垏鐗囥€佸熬杩瑰浘鐢熸垚
  - 鍏稿瀷绉戠爺鍥捐〃鏍煎紡
- 楠屾敹涓庢姤鍛?skill锛?  - benchmark 瀵规瘮
  - 椋庨櫓璇存槑
  - 涓枃缁撹妯℃澘
  - 鈥滃彲缁х画鍋氱鐮斿垽鏂?/ 鍙兘浣滄紨绀哄弬鑰冣€濈殑杈圭晫璇存槑

鍏蜂綋瑕佹眰锛?
- 姣忎釜 skill 涓嶅簲鍙槸涓€娈?prompt锛岃嚦灏戣鍖呭惈锛?  - 瑙﹀彂鏉′欢
  - 杈撳叆 contract
  - 杈撳嚭 contract
  - 楠屾敹鏍囧噯
  - 鑷冲皯 2-3 涓祴璇曞満鏅?- Skill 闇€瑕佺敱棰嗗煙涓撳鍜?Claude Code 鍏卞垱锛岃€屼笉鏄彧闈犻€氱敤妯″瀷鐢熸垚鍒濈鍚庣洿鎺ュ彂甯冦€?- Skill Studio 鏈€缁堣鏀寔杩欎簺涓撲笟 skill 鐨勬祴璇曡褰曚笌鍙戝竷杩借釜銆?
### 2.3 鏇存垚鐔熺殑 OpenFOAM 妯℃澘涓庡悗澶勭悊妯℃澘

褰撳墠浠撳簱鐨?OpenFOAM 璺緞宸茬粡閫氫簡鍩虹嚎锛屼絾杩樹笉鏄垚鐔熺鐮旀ā鏉垮簱銆?
澶栭儴闇€瑕佽ˉ褰曪細

- 鍒嗕换鍔＄被鍨嬬殑 case 妯℃澘锛?  - resistance
  - pressure distribution
  - wake field
  - 鏈潵鎵╁睍鐨?free-surface
- 妯℃澘搴斿寘鍚細
  - 鍑犱綍瀵煎叆瑙勮寖
  - blockMesh / snappyHexMesh 绛栫暐
  - turbulenceProperties
  - fvSchemes / fvSolution
  - controlDict 鎺ㄨ崘閰嶇疆
  - forces / forceCoeffs / probes / slices 绛?function objects
- 鍚庡鐞嗘ā鏉垮簲鍖呭惈锛?  - 鍥惧儚杈撳嚭鏍囧噯
  - CSV/JSON 琛ㄦ牸瀛楁
  - 涓枃鎶ュ憡寮曠敤鏍煎紡

鍏蜂綋瑕佹眰锛?
- 妯℃澘瑕佽兘瀵瑰簲鍒板叿浣撴渚嬶紝涓嶈鍙粰鈥滀竴涓竾鑳芥ā鏉库€濄€?- 姣忎釜妯℃澘瑕佹敞鏄庨€傜敤杈圭晫锛屼笉鍏佽瓒呭嚭杈圭晫鏃朵粛琚郴缁熻鐢ㄤ负鈥滅鐮旂粨鏋溾€濄€?- 妯℃澘蹇呴』鑳藉湪瀹瑰櫒鍖?sandbox 涓鐜般€?
### 2.4 杩滅▼绠楀姏涓庣敓浜у寲杩愯鐜

绉戠爺宸ヤ綔涓嶈兘闀挎湡鍋滅暀鍦ㄦ湰鍦?demo sandbox銆?
澶栭儴闇€瑕佽ˉ褰曪細

- 杩滅▼璁＄畻鑺傜偣鎴栭泦缇?- 浠诲姟闃熷垪涓庤祫婧愰厤棰濊鍒?- 闀夸换鍔¤繍琛屻€佸け璐ユ仮澶嶅拰褰掓。绛栫暐
- 缁撴灉鍥炰紶涓?artifact 鍚屾鏂规

鍏蜂綋瑕佹眰锛?
- 闇€瑕佹槑纭湰鍦?smoke run 涓庤繙绋嬫寮?run 鐨勮竟鐣屻€?- 姝ｅ紡绉戠爺 run 蹇呴』璁板綍锛?  - 杩愯鐜
  - 闀滃儚鐗堟湰
  - OpenFOAM 鐗堟湰
  - skill 鐗堟湰
  - 鍏抽敭鍙傛暟蹇収

### 2.5 棰嗗煙涓撳鍙備笌鏈哄埗

杩欐槸鍐冲畾绯荤粺鏄惁鐪熸鈥滅鐮斿彲鐢ㄢ€濈殑缁勭粐鎬ф潯浠躲€?
澶栭儴蹇呴』琛ュ綍锛?
- 璋佽礋璐ｆ渚嬪熀鍑嗕笌楠屾敹瑙勫垯
- 璋佽礋璐?OpenFOAM 妯℃澘瀹℃煡
- 璋佽礋璐?skill 鍐呭瀹℃煡
- 璋佽礋璐ｇ粨鏋滃彲淇″害鍒ゅ畾

鍏蜂綋瑕佹眰锛?
- 鑷冲皯褰㈡垚涓€涓交閲?review 鏈哄埗锛?  - `AI 璧疯崏`
  - `涓撳瀹￠槄`
  - `淇鍙戝竷`
- 娌℃湁涓撳瀹￠槄閫氳繃鐨勫唴瀹癸紝鍙兘绠楄崏绋匡紝涓嶅簲浣滀负姝ｅ紡绉戠爺瑙勮寖銆?
### 2.6 MCP 涓庡閮ㄧ煡璇?宸ュ叿鎺ュ叆

涓鸿繘涓€姝ユ彁鍗囩鐮斿伐浣滄祦锛屽閮ㄥ簲琛ュ綍鍙帴鍏ヨ兘鍔涳細

- 鏂囩尞妫€绱?- benchmark 鏁版嵁搴?- 杩滅▼鏂囦欢绯荤粺/HPC
- 涓撲笟鍚庡鐞嗗伐鍏?- 鍥㈤槦鐭ヨ瘑搴?
鍏蜂綋瑕佹眰锛?
- 杩欎簺鎺ュ叆瑕侀€氳繃 DeerFlow 鐨勬爣鍑嗘墿灞曡竟鐣屽畬鎴愶紝涓嶅啀鍙﹂€犲钩琛屾墽琛屽眰銆?- 姣忎釜鎺ュ叆瑕佹槑纭細
  - 璁块棶鏉冮檺
  - 鍙敤鑼冨洿
  - 鏄惁褰卞搷绉戠爺缁撹鍙俊搴?
## 3. 澶栭儴琛ュ綍椤圭殑楠屾敹鏍囧噯

澶栭儴鍐呭涓嶆槸鈥滄敹闆嗗埌涓€浜涙潗鏂欌€濆氨绠楀畬鎴愶紝鑷冲皯瑕佽揪鍒颁互涓嬮獙鏀舵爣鍑嗭細

### 3.1 妗堜緥涓庤鍒?
- 鑳戒互缁撴瀯鍖栨牸寮忚繘鍏ヤ粨搴?- 鑳借杩愯鏃剁洿鎺ヨ鍙?- 鑳借鎶ュ憡鍜?acceptance 閫昏緫寮曠敤
- 鑳借鏄庢潵婧愩€佽竟鐣屽拰闃堝€?
### 3.2 Skills

- 鑳藉湪 Skill Studio 涓敓鎴愩€侀獙璇併€佹墦鍖呫€佸彂甯?- 鑷冲皯鏈夋渶灏忔祴璇曞満鏅?- 杈撳嚭鍙拷韪埌 thread/artifact/run

### 3.3 妯℃澘

- 鑳藉湪 sandbox 閲屽鐜?- 鑳界ǔ瀹氱敓鎴?artifacts
- 鑳藉拰妗堜緥瑙勫垯涓€涓€瀵瑰簲

### 3.4 涓撳鍙備笌

- 鏈夋槑纭闃呰矗浠讳汉
- 鏈夌増鏈褰?- 鏈夊彂甯冩垨鎷掔粷缁撹

## 4. 浠撳簱鍐呭彲浠ョ户缁帹杩涚殑涓荤嚎

鍗充娇澶栭儴鍐呭灏氭湭鍏ㄩ儴琛ラ綈锛屽綋鍓嶄粨搴撳唴浠嶇劧鍙互缁х画鎺ㄨ繘浠ヤ笅鏂瑰悜锛?
### 4.1 Supervisor 寮洪棴鐜?
- 澶氳疆鑱婂ぉ鏀舵暃 design brief
- 鎵ц鍓嶇‘璁?- 鎵ц涓姸鎬佸洖鍐?- 鎵ц鍚庣粨鏋滃洖鏀朵笌鍐嶅喅绛?
### 4.2 妗堜緥绾ч獙鏀舵鏋?
- 鎶婃渚嬪簱浠庘€滄弿杩板瀷 metadata鈥濇彁鍗囦负鈥滃彲鎵ц楠屾敹 contract鈥?- 鍏佽鍏堟帴鍏ュ崰浣嶈鍒欙紝鍐嶉€愭鏇挎崲鎴愪笓瀹剁粰鍑虹殑姝ｅ紡闃堝€?- 璁?acceptance 閫昏緫鏀寔 `warning / blocked / ready_for_review`

### 4.3 宸ヤ綔鍙拌繃绋嬫帶鍒?
- rerun
- stop
- continue
- compare
- 闃舵鎬?review 鎿嶄綔

### 4.4 Skill Studio 娌荤悊鑳藉姏

- 鍒犻櫎
- 鐗堟湰鍖?- provenance
- 鍥炴粴

### 4.5 涓枃绉戠爺鎶ュ憡涓庡悗澶勭悊灞曠ず

- 鍥捐〃鍗犱綅缁撴瀯
- benchmark 瀵规瘮琛?- 椋庨櫓瑙ｉ噴
- 缁撹杈圭晫璇存槑

## 5. 褰撳墠宸查獙璇佺殑鍩虹鐘舵€?
浠ヤ笅鐘舵€佸凡閫氳繃鐪熷疄浠撳簱浠ｇ爜鍜屾祴璇曟牳瀹烇細

- DeerFlow 涓荤嚎宸叉帴涓婃綔鑹?CFD 鏈€灏忛棴鐜細
  - `submarine_design_brief`
  - `submarine_geometry_check`
  - `submarine_solver_dispatch`
  - `submarine_result_report`
- `task_tool` 鐨?`target_skills` 閫昏緫绗﹀悎鏃㈠畾杈圭晫锛?  - Claude 鏄惧紡浼犳墠浼氭敹绐?  - 涓嶄紶鍒?subagent 鐪嬪埌鏅€?enabled skill 姹?- 鐙珛鐨?`vibe CFD` 宸ヤ綔鍙颁笌 `Skill Studio` 宸ヤ綔鍙伴兘宸插瓨鍦?- Skill graph 宸叉帴鍏ユ湰鍦版不鐞嗗眰锛屽苟鏈?graph API 涓庡墠绔睍绀?- DeerFlow sandbox + OpenFOAM 璺緞宸插叿澶囧熀绾块摼璺?- v1 宸叉敹鍙ｅ埌 `STL-only`

瀵瑰簲浠ｇ爜閿氱偣鍖呮嫭浣嗕笉闄愪簬锛?
- `backend/packages/harness/deerflow/domain/submarine/`
- `backend/packages/harness/deerflow/tools/builtins/task_tool.py`
- `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`
- `frontend/src/components/workspace/submarine-runtime-panel.tsx`
- `backend/app/gateway/routers/skills.py`

杩涗竴姝ユ媶寮€鍚庣殑鐪熷疄鐘舵€佸涓嬶細

### 5.1 DeerFlow 涓荤嚎闂幆

- 璁捐绠€鎶ワ細
  - `backend/packages/harness/deerflow/domain/submarine/design_brief.py`
  - `backend/packages/harness/deerflow/tools/builtins/submarine_design_brief_tool.py`
- 鍑犱綍棰勬锛?  - `backend/packages/harness/deerflow/domain/submarine/geometry_check.py`
  - `backend/packages/harness/deerflow/tools/builtins/submarine_geometry_check_tool.py`
- 姹傝В娲惧彂锛?  - `backend/packages/harness/deerflow/domain/submarine/solver_dispatch.py`
  - `backend/packages/harness/deerflow/tools/builtins/submarine_solver_dispatch_tool.py`
- 缁撴灉鎶ュ憡锛?  - `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - `backend/packages/harness/deerflow/tools/builtins/submarine_result_report_tool.py`

### 5.2 Skill 璺敱杈圭晫

- `target_skills` 鍙湁 Claude Code 鏄惧紡浼犲叆鏃舵墠鏀剁獎銆?- 濡傛灉 Claude 涓嶄紶锛宻ubagent 浠嶄娇鐢ㄦ櫘閫?enabled skill 姹犮€?- 鐩稿叧閫昏緫浣嶄簬锛?  - `backend/packages/harness/deerflow/tools/builtins/task_tool.py`
  - `backend/packages/harness/deerflow/agents/lead_agent/prompt.py`

### 5.3 宸ヤ綔鍙颁笌娌荤悊灞?
- 娼滆墖宸ヤ綔鍙帮細
  - `frontend/src/app/workspace/submarine/[thread_id]/page.tsx`
  - `frontend/src/components/workspace/submarine-runtime-panel.tsx`
- Skill Studio锛?  - `frontend/src/app/workspace/skill-studio/[thread_id]/page.tsx`
  - `frontend/src/components/workspace/skill-studio-dashboard.tsx`
  - `frontend/src/components/workspace/skill-studio-workbench-panel.tsx`
- Skills graph API锛?  - `backend/app/gateway/routers/skills.py`

### 5.4 褰撳墠宸茶惤鍦扮殑缁撴灉楠屾敹鑳藉姏

鎴嚦鏈疆锛岀郴缁熷凡缁忎笉鏄彧鏈夆€滄渶缁堟姤鍛娾€濓紝杩樺叿澶囷細

- `delivery-readiness.json`
- `delivery-readiness.md`
- `final-report.json` 涓殑 `acceptance_assessment`

骞朵笖 acceptance 閫昏緫宸茬粡鏀寔锛?
- 閫氱敤 gate
  - solver completed
  - mesh quality
  - residual summary
  - planned end time
  - force coefficients
  - STL runtime contract
- 妗堜緥绾?gate
  - case required artifacts
  - case completed fraction
  - case max final residual

## 6. 褰撳墠浠嶆湭瀹屾垚鐨勫叧閿樊璺?
褰撳墠绯荤粺璺濈鈥滅湡姝ｅ彲鐢ㄤ簬绉戠爺宸ヤ綔鈥濈殑宸窛锛屾寜涓ラ噸搴︽帓搴忓涓嬶細

1. 缂哄皯妗堜緥绾?benchmark 鍜岄獙鏀惰鍒欙紝瀵艰嚧缁撴灉鍙俊搴︽棤娉曟彁鍗囧埌绉戠爺绛夌骇銆?2. Supervisor 浠嶅亸 prompt/tool 绾﹀畾锛岀己灏戞洿纭殑杩愯鐘舵€佹満銆?3. 宸ヤ綔鍙扮己灏戣繃绋嬫帶鍒惰兘鍔涳紝鏇村儚灞曠ず闈㈡澘鑰屼笉鏄爺绌跺伐浣滃彴銆?4. Skill Studio 鐨勬不鐞嗗眰杩樹笉瀹屾暣锛屾棤娉曟弧瓒抽暱鏈熺鐮旇祫浜ф矇娣€銆?5. OpenFOAM 妯℃澘鍜屽悗澶勭悊妯℃澘浠嶅亸鍩虹嚎婕旂ず銆?
## 7. 鏈疆浠撳簱鍐呮帹杩涚洰鏍?
鏈疆浼樺厛鎺ㄨ繘涓€涓渶鍏抽敭銆佷笖褰撳墠浠撳簱鍐呯珛鍒昏兘鍋氱殑鏂瑰悜锛?
- 鎶婂綋鍓嶇粨鏋滈獙鏀朵粠鈥滈€氱敤浜や粯闂ㄦ帶鈥濇帹杩涘埌鈥滄渚嬬骇绉戠爺楠屾敹妗嗘灦鈥濈殑绗竴姝ャ€?
鏈疆涓嶈瘯鍥惧嚟绌哄垱閫?benchmark 鐪熷€硷紝鑰屾槸鍏堟妸浠撳簱鍐呯殑妗堜緥 contract 缁撴瀯鎼捣鏉ワ紝浣跨郴缁熷彲浠ワ細

- 浠庢渚嬪簱璇诲彇楠屾敹 profile
- 鍦ㄧ粨鏋滄姤鍛婁腑寮曠敤妗堜緥绾ч槇鍊?- 缁欏嚭鏇存竻鏅扮殑 case-aware acceptance gate

杩欎竴姝ュ畬鎴愬悗锛屽悗缁閮ㄤ笓瀹惰ˉ褰曠殑瑙勫垯鎵嶈兘鑷劧鎺ュ叆锛屼笉闇€瑕侀噸鍐欐暣鏉¤繍琛屾椂銆?
## 8. 鏈疆鎺ㄨ繘璁板綍涓庡綋鍓嶈缁嗙姸鎬?
### 8.1 鏈疆鏂板鐨勪粨搴撳唴鑳藉姏

鏈疆宸插畬鎴愪袱绫绘帹杩涳細

1. 鏂囨。鍖栨⒊鐞嗭細
   - 鏄庣‘澶栭儴蹇呴』琛ュ綍椤?   - 鏄庣‘澶栭儴鍐呭鐨勫叿浣撻獙鏀惰姹?   - 鏄庣‘浠撳簱鍐呭彲缁х画鎺ㄨ繘鏂瑰悜
2. 浠ｇ爜鎺ㄨ繘锛?   - 鎶婃渚嬪簱浠庘€滄弿杩板瀷 metadata鈥濆悜鈥滄渚嬬骇楠屾敹 contract鈥濇帹杩涗簡涓€姝?   - 璁╃粨鏋滄姤鍛婂紑濮嬭鍙?case-specific acceptance profile
   - 璁?acceptance assessment 鑳芥牴鎹渚嬭鍒欑粰鍑烘洿涓ユ牸鐨勫垽瀹?
### 8.2 鏈疆鐪熷疄淇敼鐨勬枃浠?
#### 鏂囨。

- `docs/archive/superpowers/specs/2026-03-27-vibe-cfd-research-readiness.md`

#### 浠撳簱鍐呭疄鐜?
- `backend/packages/harness/deerflow/domain/submarine/models.py`
  - 鏂板 `SubmarineCaseAcceptanceProfile`
  - `SubmarineCase` 澧炲姞 `acceptance_profile`
- `domain/submarine/cases/index.json`
  - 涓洪鎵瑰叧閿渚嬭ˉ鍏ユ渚嬬骇 acceptance profile
- `backend/packages/harness/deerflow/domain/submarine/reporting.py`
  - 鏂板 selected case 瑙ｆ瀽
  - 鏂板 case-aware acceptance gates
  - `final-report.json` 鏂板 `selected_case_acceptance_profile`

#### 娴嬭瘯

- `backend/tests/test_submarine_domain_assets.py`
- `backend/tests/test_submarine_result_report_tool.py`

### 8.3 鏈疆宸查獙璇佺殑琛屼负

浠ヤ笅琛屼负宸查€氳繃鐪熷疄娴嬭瘯楠岃瘉锛?
- 妗堜緥搴撹兘鍔犺浇 `acceptance_profile`
- `darpa_suboff_bare_hull_resistance` 宸插甫鏈夌粨鏋勫寲 case profile
- 缁撴灉鎶ュ憡浼氭妸妗堜緥 profile 鍐欏叆 `final-report.json`
- 褰撴渚嬮槇鍊艰绐佺牬鏃讹紝`acceptance_assessment` 浼氳浆涓?`blocked`
- 涔嬪墠宸插瓨鍦ㄧ殑閫氱敤 delivery readiness 娴佺▼浠嶇劧淇濇寔鍙敤

### 8.4 鏈疆鎵ц鐨勯獙璇?
鍚庣锛?
- `uv run pytest tests/test_submarine_design_brief_tool.py tests/test_submarine_geometry_check_tool.py tests/test_submarine_solver_dispatch_tool.py tests/test_submarine_result_report_tool.py tests/test_task_tool_core_logic.py tests/test_lead_agent_prompt_skill_routing.py tests/test_skill_relationships.py tests/test_skills_graph_router.py tests/test_skills_publish_router.py tests/test_submarine_subagents.py tests/test_submarine_skill_studio_tool.py tests/test_submarine_domain_assets.py tests/test_submarine_skills_presence.py -q`
- 缁撴灉锛歚55 passed`

鍓嶇锛?
- `node --experimental-strip-types --test src/app/workspace/submarine/submarine-workbench-layout.test.ts src/app/workspace/skill-studio/skill-studio-workbench-layout.test.ts src/components/workspace/submarine-runtime-panel.utils.test.ts src/components/workspace/submarine-runtime-panel.trends.test.ts src/components/workspace/skill-graph.utils.test.ts src/components/workspace/skill-studio-dashboard.utils.test.ts src/components/workspace/skill-studio-workbench.utils.test.ts`
- 缁撴灉锛歚24 passed`

绫诲瀷妫€鏌ワ細

- `frontend/node_modules/.bin/tsc.cmd --noEmit`
- 缁撴灉锛氶€氳繃

### 8.5 褰撳墠椤圭洰鐨勮缁嗙姸鎬佸垽鏂?
#### 宸茬粡鍋氬埌鐨?
- DeerFlow 涓荤嚎娼滆墖 CFD 鏈€灏忛棴鐜凡鎴愬瀷銆?- `vibe CFD` 涓?`Skill Studio` 涓や釜宸ヤ綔鍙伴兘宸茶惤鍦ㄥ悓涓€ DeerFlow thread/artifact/chat 浣撶郴涓嬨€?- `target_skills` 杈圭晫涓?skill graph 瀹氫綅绗﹀悎鏃㈠畾鍐崇瓥銆?- `STL-only` 杈圭晫宸插湪杩愯鏃躲€佸叕寮€ skill 鍜屾渚嬪簱灞傞潰鏀跺彛銆?- 缁撴灉鎶ュ憡宸茬粡涓嶅彧鏄€滅敓鎴愪竴浠?md/html鈥濓紝杩樺叿澶囩粨鏋勫寲 acceptance layer銆?- acceptance layer 宸插紑濮嬫敮鎸佹渚嬬骇绉戠爺楠屾敹 skeleton銆?
#### 浠嶇劧鍙槸鍗婃垚鍝佺殑

- 妗堜緥绾?acceptance profile 鐜板湪杩樻槸绗竴鐗?skeleton锛屽彧瑕嗙洊褰撳墠绯荤粺鑳界洿鎺ヨ鍙栫殑鎸囨爣銆?- benchmark 鐪熷€笺€佹枃鐚宸€佺綉鏍肩嫭绔嬫€ц鍒欒繕娌℃湁鐪熸鎺ュ叆銆?- Supervisor 鐨勫杞敹鏁涘拰闃舵闂ㄦ帶杩樺亸 prompt 椹卞姩锛屼笉鏄畬鏁寸姸鎬佹満銆?- 宸ヤ綔鍙扮洰鍓嶄粛鍋忓睍绀洪潰锛岃繃绋嬫帶鍒惰繕涓嶈冻銆?- Skill Studio 娌荤悊灞傝繕涓嶅瀹屾暣銆?
#### 褰撳墠涓昏椋庨櫓

1. 娌℃湁澶栭儴 benchmark 鍜屼笓瀹惰鍒欐椂锛宑ase-aware acceptance 浠嶇劧鍙槸鈥滅鐮旀鏋垛€濓紝杩樹笉鏄寮忕鐮斿垽瀹氥€?2. 鏈湴 sandbox 鍩虹嚎鍙敤涓嶇瓑浜庤繙绋嬬敓浜х畻鍔涘彲鐢ㄣ€?3. 缁撴灉鍙鍖栧拰鍚庡鐞嗘ā鏉夸粛涓嶈冻浠ユ敮鎾戦珮璐ㄩ噺绉戠爺姹囨姤銆?4. 褰撳墠妗堜緥绾ц鍒欎富瑕佽鐩栨暟鍊奸棬妲涳紝灏氭湭瑕嗙洊鍥捐〃銆佸姣旀洸绾垮拰鐮旂┒缁撹杈圭晫銆?
### 8.6 涓嬩竴闃舵鏈€鍊煎緱缁х画鎺ㄨ繘鐨勪粨搴撳唴浜嬮」

鎸変紭鍏堢骇寤鸿缁х画鎺ㄨ繘锛?
1. 鎶婃渚嬬骇 acceptance profile 浠?skeleton 鎵╁睍涓烘洿瀹屾暣鐨?case contract锛?   - benchmark comparison
   - mesh independence
   - report-required sections
2. 寮哄寲 Supervisor 闂幆锛?   - design brief 澶氳疆鏀舵暃
   - 鎵ц鍓嶇‘璁?   - 鎵ц鍚?review gate
3. 缁欏伐浣滃彴琛ヨ繃绋嬫帶鍒讹細
   - rerun
   - stop
   - continue
   - compare
4. 缁?Skill Studio 琛ユ不鐞嗗眰锛?   - delete
   - version history
   - rollback

## 9. 2026-03-27 Benchmark-Aware 鎺ㄨ繘琛ヨ

### 9.1 鏈疆缁х画鎺ㄨ繘鐨勭洰鏍?
鏈疆娌℃湁鍘绘墿鏂扮殑鐣岄潰澹冲瓙锛岃€屾槸缁х画琛モ€滅鐮斿彲淇″害鈥濊繖涓€灞傘€傚師鍥犳槸褰撳墠浠撳簱铏界劧宸茬粡鍏峰 DeerFlow 涓荤嚎涓嬬殑娼滆墖 CFD 鍩虹嚎闂幆锛屼絾缁撴灉灞備粛鐒剁己灏戠湡姝ｅ彲鎵ц鐨?benchmark-aware 鍒ゆ柇銆?
杩欎竴杞殑鎺ㄨ繘鐩爣琚敹鏁涗负涓変欢浜嬶細

1. 鐢ㄧ湡瀹?STL 鏂囦欢 `C:\Users\D0n9\Desktop\suboff_solid.stl` 澶嶆牳褰撳墠鍑犱綍璇嗗埆鍜?case 鍖归厤鏄惁姝ｇ‘銆?2. 缁?`darpa_suboff_bare_hull_resistance` 琛ュ叆绗竴鏉″彲鎵ц benchmark target銆?3. 璁?`submarine_result_report` 鍦ㄥ伐鍐靛尮閰嶆椂鑷姩鐢熸垚 benchmark comparison锛屽苟鎶婄粨鏋滃啓鍏?`acceptance_assessment`銆?
### 9.2 鍩轰簬鐪熷疄 STL 鐨勫鏍哥粨鏋?
浣跨敤浠撳簱涓殑鍑犱綍璇嗗埆涓?case ranking 閫昏緫澶勭悊 `C:\Users\D0n9\Desktop\suboff_solid.stl` 鍚庯紝寰楀埌濡備笅缁撴灉锛?
- file_name: `suboff_solid.stl`
- input_format: `stl`
- geometry_family: `DARPA SUBOFF`
- estimated_length_m: `4.356`
- triangle_count: `32760`
- top_case_id: `darpa_suboff_bare_hull_resistance`
- top_case_score: `8.9`

杩欒鏄庡綋鍓嶄富閾句腑鐨勶細

- `backend/packages/harness/deerflow/domain/submarine/geometry_check.py`
- `backend/packages/harness/deerflow/domain/submarine/library.py`

宸茬粡鑳芥妸璇?STL 绋冲畾璇嗗埆杩?SUBOFF 瀹舵棌锛屽苟鎶婄涓€鎺ㄨ崘妗堜緥钀藉埌闃诲姏鍩虹嚎 case锛岃€屼笉鏄敊璇垎娴佸埌鍒殑妯℃澘銆?
### 9.3 鏈疆鎺ュ叆鐨?benchmark 鏉ユ簮涓庤竟鐣?
鏈疆浣跨敤浜嗗彲鍏紑璁块棶銆佸彲杩借釜鐨勮祫鏂欏仛绗竴鐗?benchmark 鎺ュ叆锛?
- 鍑犱綍涓庡疄楠岃鍒掑厓鏁版嵁锛?  - `https://ntrl.ntis.gov/NTRL/dashboard/searchResults/titleDetail/ADA210642.xhtml`
  - `https://ntrl.ntis.gov/NTRL/dashboard/searchResults/titleDetail/ADA359226.xhtml`
- 褰撳墠鐩存帴鎺ュ叆鐨勯樆鍔涚郴鏁板弬鑰冨€兼潵婧愶細
  - `https://pure.port.ac.uk/ws/portalfiles/portal/110702250/Hydrodynamic_parameter_estimation_of_DARPA_SUBOFF.pdf`

鏈疆钀藉埌浠ｇ爜閲岀殑 benchmark target 涓猴細

- case: `darpa_suboff_bare_hull_resistance`
- metric_id: `cd_at_3_05_mps`
- quantity: `Cd`
- reference_value: `0.00314`
- inlet_velocity_mps: `3.05`
- relative_tolerance: `0.1`
- on_miss_status: `blocked`

闇€瑕佹槑纭殑鏄細

- 杩欎笉鏄畬鏁寸殑 DARPA SUBOFF 绉戠爺楠屾敹鍖呫€?- 瀹冨彧鏄涓€鏉＄湡姝ｆ帴杩?DeerFlow 涓婚摼鐨?benchmark rule銆?- 鍚庣画浠嶇劧闇€瑕侀鍩熶笓瀹惰ˉ鍏ユ洿澶?benchmark銆佸宸緷鎹€佺綉鏍肩嫭绔嬫€ц鍒欏拰鍥捐〃绾ч獙鏀惰鍒欍€?
### 9.4 鏈疆鐪熷疄浠ｇ爜鏀瑰姩

#### 1. 鎵╁睍妗堜緥楠屾敹 schema

鏂囦欢锛?
- `backend/packages/harness/deerflow/domain/submarine/models.py`

鏀瑰姩锛?
- 鏂板 `SubmarineBenchmarkTarget`
- 鍦?`SubmarineCaseAcceptanceProfile` 涓柊澧?`benchmark_targets`

#### 2. 鎶?benchmark target 鎺ュ叆妗堜緥搴?
鏂囦欢锛?
- `domain/submarine/cases/index.json`

鏀瑰姩锛?
- 涓?`darpa_suboff_bare_hull_resistance` 琛ュ叆缁撴瀯鍖?benchmark target
- 灏嗚 case 鐨勫弬鑰冩潵婧愪粠鍗犱綅閾炬帴鏀舵暃鍒扮湡瀹炲叕寮€鏉ユ簮
- 鍚屾椂鎶婅鏂囦欢涓師鍏堝瓨鍦ㄧ殑涓枃涔辩爜鍨?summary 涓€骞舵敹鍙ｄ负姝ｅ父鍙鏂囨湰

#### 3. 璁╃粨鏋滄姤鍛婄敓鎴?benchmark comparisons

鏂囦欢锛?
- `backend/packages/harness/deerflow/domain/submarine/reporting.py`

鏀瑰姩锛?
- 鏂板 benchmark observed value 瑙ｆ瀽閫昏緫
- 鏂板 benchmark target 璇勪及閫昏緫
- 鍦?`acceptance_assessment` 涓柊澧?`benchmark_comparisons`
- 瀵瑰懡涓殑 benchmark target 鑷姩鐢熸垚瀵瑰簲 gate锛屼緥濡傦細
  - `benchmark_cd_at_3_05_mps`
- benchmark miss 浼氭寜鐓?profile 閰嶇疆杩涘叆 `warning` 鎴?`blocked`
- delivery readiness 鐨?markdown/html 浜х墿涔熶細甯﹀嚭 benchmark comparison 鎽樿

### 9.5 鏈疆鏂板鍜屾墿灞曠殑娴嬭瘯

鏂囦欢锛?
- `backend/tests/test_submarine_domain_assets.py`
- `backend/tests/test_submarine_result_report_tool.py`

鍏抽敭瑕嗙洊鍖呮嫭锛?
- `SubmarineCaseAcceptanceProfile` 鑳藉惁鍔犺浇 `benchmark_targets`
- `darpa_suboff_bare_hull_resistance` 鏄惁鏆撮湶 `cd_at_3_05_mps`
- 褰?`inlet_velocity_mps = 3.05` 涓?`Cd` 鎺ヨ繎 `0.00314` 鏃讹紝鏄惁鐢熸垚 `passed` 鐨?benchmark comparison
- 褰撳悓涓€宸ュ喌涓?`Cd` 鍋忕杩囧ぇ鏃讹紝鏄惁鐢熸垚 `blocked` 鐨?benchmark gate锛屽苟鎶?run 鏍囦负 `blocked`

### 9.6 鏈疆楠岃瘉缁撴灉

#### 瀹氬悜 TDD 楠岃瘉

- `uv run pytest tests/test_submarine_domain_assets.py::test_submarine_case_library_exposes_case_acceptance_profiles -q`
- `uv run pytest tests/test_submarine_result_report_tool.py::test_submarine_result_report_adds_benchmark_comparison_for_matching_case -q`
- `uv run pytest tests/test_submarine_result_report_tool.py::test_submarine_result_report_blocks_when_benchmark_miss_exceeds_tolerance -q`

缁撴灉锛?
- 鍏堢孩鍚庣豢锛岀鍚?TDD 棰勬湡

#### 娼滆墖鍩熷洖褰?
- `uv run pytest tests -q -k submarine`

缁撴灉锛?
- `36 passed, 730 deselected, 1 warning`

璇存槑锛?
- warning 浠嶆潵鑷?`backend/packages/harness/deerflow/agents/memory/updater.py` 涓棦鏈夌殑 `datetime.utcnow()` deprecation锛屼笌鏈疆鏀瑰姩鏃犲叧銆?
#### 鍓嶇宸ヤ綔鍙伴獙璇?
- `node --experimental-strip-types --test src/components/workspace/submarine-runtime-panel.utils.test.ts`
- `node_modules/.bin/tsc.cmd --noEmit`

缁撴灉锛?
- `submarine-runtime-panel.utils.test.ts` 閫氳繃
- `frontend` TypeScript 绫诲瀷妫€鏌ラ€氳繃

璇存槑锛?
- benchmark comparison 鐜板湪宸茬粡鑳戒粠 `acceptance_assessment.benchmark_comparisons` 杩涘叆鍓嶇 summary锛屽苟鏄剧ず鍦?`submarine-runtime-panel` 鐨勫仴搴烽潰鏉块噷銆?
### 9.7 褰撳墠椤圭洰鐘舵€佺殑鏂板鍒ゆ柇

鍦ㄦ湰杞?benchmark-aware 鎺ㄨ繘涔嬪悗锛屽彲浠ユ妸椤圭洰鐘舵€佹洿鏂颁负锛?
- 褰撳墠绯荤粺宸茬粡涓嶄粎鏈夆€滅粨鏋勫寲 delivery readiness鈥濓紝杩樺叿澶団€滅涓€鏉＄湡姝ｅ彲鎵ц鐨?case benchmark comparison鈥濄€?- 杩欐剰鍛崇潃浠撳簱宸茬粡杩堝嚭浜嗕粠鈥滃伐绋?gate鈥濊蛋鍚戔€滅鐮?gate鈥濈殑绗竴姝ャ€?- 浣嗗綋鍓嶄粛鐒跺彧鏄竴鏉＄ず鑼冩€?benchmark rule锛屼笉瓒充互鍗曠嫭鏀拺绉戠爺缁撹銆?
鏇村叿浣撳湴璇达細

- 宸插仛鍒帮細
  - DeerFlow 涓荤嚎涓嬬殑娼滆墖 CFD 缁撴灉鎶ュ憡鍙互璇诲彇妗堜緥 benchmark rule 骞舵墽琛屾瘮杈冦€?  - benchmark 缁撴灉浼氳繘鍏?`acceptance_assessment`銆乨elivery readiness markdown/html 鍜屾渶缁?JSON 鎶ュ憡銆?  - 鐪熷疄 SUBOFF STL 宸茶兘瀵逛笂 SUBOFF 闃诲姏鍩虹嚎 case銆?- 浠嶆湭鍋氬埌锛?  - 澶?benchmark 鑱斿悎楠屾敹
  - 缃戞牸鐙珛鎬ч獙鏀?  - 鍥捐〃绾?benchmark 瀵规瘮
  - 杩滅▼姝ｅ紡绠楀姏涓庨暱浠诲姟娌荤悊
  - 棰嗗煙涓撳瀹℃牳鍚庣殑姝ｅ紡楠屾敹鍖?
### 9.8 涓嬩竴姝ユ渶鍊煎緱缁х画鎺ㄨ繘鐨勪粨搴撳唴浜嬮」

鎸変紭鍏堢骇锛屼笅涓€姝ュ缓璁户缁帹杩涳細

1. 灏?benchmark-aware acceptance 浠庡崟鏉¤鍒欐墿鎴愬彲澶嶇敤 contract
   - 鏀寔澶氫釜 benchmark target
   - 鏀寔鍥捐〃/鏇茬嚎绫?required outputs
   - 鏀寔 mesh-independence 鍗犱綅瑙勫垯
2. 鎵╁睍宸ヤ綔鍙颁腑鐨?benchmark 灞曠ず娣卞害
   - 褰撳墠宸茬粡鑳藉湪 `submarine-runtime-panel` 涓洿鎺ョ湅鍒?benchmark pass/block 鐘舵€?   - 涓嬩竴姝ュ簲琛?benchmark 鏉ユ簮銆佽宸櫨鍒嗘瘮鍜屽弬鑰冨€艰鏄?3. 缁х画寮哄寲 Supervisor 闂幆
   - 鍦?design brief 鏀舵暃銆佹墽琛岃鍙€佺粨鏋滃洖鏀朵箣闂磋ˉ鏇寸‖鐨勮繍琛岀姸鎬?4. 涓?Skill Studio 琛ョ増鏈笌鍥炴粴娌荤悊
   - 璁╁悗缁笓瀹跺叡鍒涚殑涓撲笟 CFD skills 鑳借瀹夊叏鍙戝竷鍜屽洖婊?
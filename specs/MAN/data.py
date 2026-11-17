"""Manchukuo board data, extracted verbatim from the seed scripts (man_common, man_systems,
man_sites, man_map, man_polgui, man_ui_text, man_systems2, man_build) by a one-off dump.

Edit freely: this file is now the source of truth for the MAN boards."""

STATES = [716, 715, 328, 717, 714, 761, 610, 611, 612, 1043]

SNAME = {716: 'Liaoning',
 715: 'Liaobei',
 328: 'Kirin',
 717: 'Sungkiang',
 714: 'Heilungkiang',
 761: 'Hulunbuir',
 610: 'Jehol',
 611: 'Chahar',
 612: 'Xilingol',
 1043: 'Pailingmiao'}

ZONES = {'hi': [716, 328, 717, 714], 'min': [716, 715, 328, 717, 714, 761, 610], 'pow': [716, 328, 717], 'set': [717, 714, 761, 328, 715, 611, 612]}

QUOTAS = [('steel', 'Iron and Steel'), ('coal', 'Coal and Liquid Fuel'), ('power', 'Electric Power'), ('mach', 'Machinery and Munitions')]

BROKERS = ['kw', 'gab', 'ind', 'mgy', 'smr']

BK = {'kw': ('Kwantung Army Staff', 'gab'),
 'gab': ('General Affairs Board', 'kw'),
 'ind': ('Ministry of Industry', None),
 'mgy': ('Mangyo', 'smr'),
 'smr': ('Mantetsu', 'mgy')}

HOLDERS = {'kw': ['Itagaki Seishiro', 'Tojo Hideki', 'Isogai Rensuke'],
 'gab': ['Hoshino Naoki', 'Takebe Rokuzo'],
 'ind': ['Kishi Nobusuke', 'Shiina Etsusaburo'],
 'mgy': ['Ayukawa Yoshisuke', 'Takasaki Tatsunosuke'],
 'smr': ['Matsuoka Yosuke', 'Omura Takuichi']}

VACANT = {'ind': 'Vacant: awaiting a Tokyo bureaucrat', 'mgy': 'Not yet founded'}

REQ_NAMES = {'kw': ('Secure the Railway Zone', 'Feed the Kwantung Army'),
 'gab': ('Fund the Concordia Budget', 'Clean the Ministries'),
 'ind': ('Meet the Steel Target', 'Zone New Ground'),
 'mgy': ('Machinery for Mangyo', 'A Free Hand for Mangyo'),
 'smr': ('Lay More Track', 'Coal for the Railways')}

BANDS = {1: ('First Route Army', 'Yang Jingyu', [715, 328], False),
 2: ('Second Route Army', 'Zhou Baozhong', [717, 328], True),
 3: ('Third Route Army', 'Zhao Shangzhi', [714, 717], True)}

SITES = [(716, 'min', 'Gongchangling Magnetite Mines'),
 (716, 'min', 'Fushun Oil Shale Retorts'),
 (716, 'hi', 'The Tiexi Industrial District'),
 (716, 'hi', 'Antung Light Metals Works'),
 (715, 'min', 'The Fuxin Open Pit'),
 (715, 'min', 'Yangjiazhangzi Molybdenum'),
 (328, 'hi', 'The Great Hsinking Plan'),
 (328, 'hi', 'Harbin Railway Workshops'),
 (328, 'min', 'The Dongbiandao Development Company'),
 (328, 'pow', 'Kirin Electro-Chemical Works'),
 (717, 'min', 'Hegang Collieries'),
 (717, 'min', 'Jixi and Mishan Coal'),
 (717, 'hi', 'Mudanjiang Garrison Works'),
 (717, 'pow', 'Jingpo Lake Hydro Station'),
 (714, 'min', 'The Heihe and Mohe Gold Fields'),
 (714, 'hi', 'Qiqihar Machine Works'),
 (761, 'min', 'Jalainur Collieries'),
 (761, 'set', 'Hailar Meat and Hides'),
 (610, 'min', 'Beipiao Collieries'),
 (611, 'set', 'The Chahar Wool Trade'),
 (612, 'set', 'Xilingol Remount Depots')]

FOUND = {716: 'Gongchangling magnetite and the Fushun shale beds; room for an industrial district at Tiexi and light metals at Antung',
 715: 'the Fuxin coalfield and molybdenum at Yangjiazhangzi',
 328: "Tonghua iron and coal for a Dongbiandao company; sites for Hsinking's industrial quarter, the Harbin workshops and "
      'electro-chemistry below Fengman',
 717: 'the Hegang and Jixi coalfields, a garrison works site at Mudanjiang and a hydro site at Jingpo Lake',
 714: 'gold in the Amur valleys and a machine works site at Qiqihar',
 761: 'Jalainur lignite and the Barga herds',
 610: 'coking coal at Beipiao',
 611: 'the Chahar wool trade',
 612: 'remount pastures on the Xilingol steppe',
 1043: 'nothing worth the expense'}

ZNAME_S = {'hi': 'Heavy Industry Zone', 'min': 'Mining District', 'pow': 'Power and Water District', 'set': 'Settlement and Grain Zone'}

ZICON = {'hi': 'GFX_decision_generic_factory',
 'min': 'GFX_decision_generic_merge_plant_materiel',
 'pow': 'GFX_decision_hol_inundate_water_lines',
 'set': 'GFX_decision_generic_colonial_administration'}

ZCOST = 25

SCOST_PP = 15

SCOST_LAB = 5

SDAYS = 45

LIFT = 50

SEC = [('gar', 'Police Garrison', 'GFX_decision_generic_protection', 0, 15, 0, 0, '', 0),
 ('sw', 'Punitive Sweep', 'GFX_decision_generic_army_support', 30, 10, 0, 15, '', 60),
 ('hm', 'Collective Hamlets', 'GFX_decision_oppression', 120, 40, 10, 0, 'MAN_sec_collective_hamlets', 0),
 ('bh', 'Blockhouse Line', 'GFX_decision_generic_fortification', 60, 30, 10, 0, 'MAN_sec_blockhouses', 0),
 ('inf', 'Informant Network', 'GFX_decision_generic_police_action', 0, 20, 0, 0, 'MAN_sec_kempeitai', 0)]

SEC_DONE_FLAG = {'gar': 'MAN_garrisoned', 'hm': 'MAN_hamlets', 'bh': 'MAN_blockhouses', 'inf': 'MAN_informants'}

GAR_MP = 5000

GAR_DAYS = 365

COURT_COST = {'kw': 30, 'gab': 30, 'ind': 40, 'mgy': 30, 'smr': 30}

BARS = {'gold': (205, 160, 55), 'blue': (85, 140, 215), 'red': (190, 55, 45), 'green': (85, 170, 80)}

TTI = {'kw': 'Commands Manchukuo in all but name. Wants the bandits crushed and the arsenals working for the army.',
 'gab': 'The Japanese-run cabinet secretariat that really governs. Wants money and order.',
 'ind': "The reform bureaucrats' planning ministry. Drives the Five-Year Plan.",
 'mgy': "Ayukawa Yoshisuke's Manchurian Industrial Development Company, built on Nissan capital.",
 'smr': 'The South Manchuria Railway Company: railways, mines, research and a state within the state.'}

ACCENT = {'kw': (170, 52, 42), 'gab': (70, 110, 175), 'ind': (195, 152, 60), 'mgy': (55, 140, 128), 'smr': (150, 40, 62)}

EMBLEM = {'kw': 'GFX_MAN_an_army_with_a_state-905635',
 'gab': 'GFX_focus_MAN_pol_gab_state',
 'ind': 'GFX_focus_MAN_eco_kishi_arrives',
 'mgy': 'GFX_focus_MAN_eco_found_mangyo',
 'smr': 'GFX_MAN_manetsu_research_department-905555'}

TIER_COL = [(96, 128, 92), (196, 170, 70), (214, 122, 48), (186, 52, 40), (110, 24, 26)]

PLAN_COL = [(88, 84, 76), (150, 138, 104), (196, 186, 152), (182, 76, 52), (150, 112, 64), (72, 124, 182), (104, 152, 78)]

PLAN_NAMES = ['Unsurveyed',
 'Survey under way',
 'Surveyed',
 'Heavy Industry Zone',
 'Mining District',
 'Power and Water District',
 'Settlement and Grain Zone']

PLAN_FLAGS = [None, 'MAN_svy_on', 'MAN_surveyed', 'MAN_zone_hi', 'MAN_zone_min', 'MAN_zone_pow', 'MAN_zone_set']

UI_OVR = {'MAN_PL_HELP_TT': '§YThe Industrial Development Plan§!\\n£white_dot §YSurvey§! a province, then §Ydesignate§! it as Heavy Industry, '
                   'Mining, Power or Settlement\\n£white_dot Build its §Ysites§! and projects: they cost £pol_power, £manpower_texticon '
                   '§Ylabour§! and £civ_factory while they run\\n£white_dot Finished work fills the four §Yquotas§!\\n£white_dot Output is '
                   'cut by £pol_violence §Obanditry§! and raised by £prod_eff §Yplanning efficiency§!\\n£white_dot §YProduction runs§! and '
                   'trade sites pay £civ_factory_output §YEconomic Capacity Surplus§!\\n£white_dot Labour drives and labour gangs raise '
                   '£manpower_texticon §YLabour levy pressure§! (now §Y[?MAN_levy|0]§!): every point costs §R0.015%§! stability a week, '
                   'and it fades by §Y6%§! a week\\n£white_dot Each running project ties up §Y0.5k§! £manpower_texticon §Ylabour§! a week, '
                   'and idle workers above §Y60k§! drift home\\n£white_dot Every finished site, project or megaproject risks an '
                   '§Rindustrial accident§!: §Y20%§! an accident (stability and manpower lost), §Y10%§! a disaster (also war support and a '
                   '£civ_factory civilian factory)\\n£white_dot The §YAnnual Review§! needs §Y20%§! more total fulfilment each plan year: '
                   'passing raises £army_experience §LKwantung Army patience§!, failing lowers it\\n£white_dot At §Y100%§! by the third '
                   'review or later, the Plan closes §Gahead of schedule§!',
 'MAN_PB_HELP_TT': '£pol_idea §LThe Hsinking Bureaucracy§!\\n£influence_texticon Favour (§Y0§! to §Y100§!) with each power centre feeds '
                   'the spirit:\\n£white_dot §LKwantung Army Staff§!: £organization_texticon organisation, £pol_violence stronger '
                   '§OPunitive Sweeps§!\\n£white_dot §LGeneral Affairs Board§!: £pol_power political power\\n£white_dot §LMinistry of '
                   'Industry§!: £construction_speed_icon construction speed, £prod_eff §Yplanning efficiency§!\\n£white_dot §LMangyo§!: '
                   '£industry_texticon factory output\\n£white_dot §LMantetsu§!: £infrastructure_texticon infrastructure '
                   'speed\\n£white_dot £influence_texticon Favour drifts back to its §Lresting level§! (§Y40§!, raised by some '
                   'focuses)\\n£white_dot A man leaving for Tokyo becomes a £increase_texticon §Gpatron§! at §Y60§! favour or more, a '
                   '£decrease_texticon §Renemy§! at §Y30§! or less',
 'MAN_PB_PAT_TT': '£army_experience §LKwantung Army patience§!\\n£white_dot Above §Y50§!: §Gmore§! stability and war support. Below: '
                  '§Rless§!\\n£white_dot Below §Y40§!: §Rweekly§! stability loss, worse the lower it falls\\n£white_dot Rises with '
                  '§LKwantung Army Staff§! favour\\n£white_dot Falls while average £pol_violence §Obanditry§! is over §Y30§!\\n£white_dot '
                  'Reviews, requests and focuses move it sharply\\n£white_dot Below §R15§!: the Army intervenes in the government',
 'MAN_SB_HELP_TT': '§OPublic Security§!\\n£white_dot Every province has £pol_violence §Obanditry§! from §Y0§! to §Y100§!\\n£white_dot '
                   "Penalties start at §Y25§! and worsen at §Y45§!, §Y65§! and §Y85§!\\n£white_dot It cuts the Plan's output there and "
                   'drains £army_experience §LKwantung Army patience§!\\n£white_dot Average £pol_violence §Obanditry§! costs §R0.2%§! '
                   'stability per point, and above §Y25§! also stability §Revery week§!\\n£white_dot §RRaised by§!: §Ogrievances§! and the '
                   '£nato_unit_irregular_infantry_icon_small §ORoute Armies§!\\n£white_dot A §Ogrievance§! is local anger from reprisals, '
                   'forced labour, settlers or requisitions: §R+0.15§! £pol_violence §Obanditry§! growth a week in that province until it '
                   'fades (§Y120§! to §Y365§! days)\\n£white_dot §GLowered by§!: §OPolice Garrisons§!, blockhouses, §OCollective '
                   'Hamlets§!, informants and §OPunitive Sweeps§!',
 'MAN_plan_cat_desc': 'Survey and designate provinces, build their sites, and fill the four §Yquotas§! before each §YAnnual Review§!.',
 'MAN_politics_cat_desc': 'Five Japanese power centres run Manchukuo. Court them, answer their requests and keep the £army_experience '
                          '§LKwantung Army patience§!.',
 'MAN_security_cat_desc': 'The £nato_unit_irregular_infantry_icon_small §ORoute Armies§! of the Northeast Anti-Japanese United Army still '
                          'hold the forests. £pol_violence §OBanditry§! slows construction, resources and the Plan.',
 'MAN_SB_BN_1_TT': '£nato_unit_irregular_infantry_icon_small §OFirst Route Army§! (Yang Jingyu)\\n£white_dot Home: §CLiaobei§!, '
                   '§CKirin§!\\n£white_dot Its strength raises £pol_violence §Obanditry§! there every week\\n£white_dot Worn down by '
                   '§OPunitive Sweeps§! and §OCollective Hamlets§!\\n£white_dot §OSurrender Campaigns§! peel men away',
 'MAN_SB_BN_2_TT': '£nato_unit_irregular_infantry_icon_small §OSecond Route Army§! (Zhou Baozhong)\\n£white_dot Home: §CSungkiang§!, '
                   '§CKirin§!\\n£white_dot Its strength raises £pol_violence §Obanditry§! there every week\\n£white_dot Worn down by '
                   '§OPunitive Sweeps§! and §OCollective Hamlets§!\\n£white_dot §OSurrender Campaigns§! peel men away\\n£white_dot When '
                   'broken it may flee across the Amur, and return if the Soviets go to war',
 'MAN_SB_BN_3_TT': '£nato_unit_irregular_infantry_icon_small §OThird Route Army§! (Zhao Shangzhi)\\n£white_dot Home: §CHeilungkiang§!, '
                   '§CSungkiang§!\\n£white_dot Its strength raises £pol_violence §Obanditry§! there every week\\n£white_dot Worn down by '
                   '§OPunitive Sweeps§! and §OCollective Hamlets§!\\n£white_dot §OSurrender Campaigns§! peel men away\\n£white_dot When '
                   'broken it may flee across the Amur, and return if the Soviets go to war'}

QI = {'STEEL': '£resources_strip|5 §YIron and Steel§!',
 'COAL': '£resources_strip|7 §YCoal and Liquid Fuel§!',
 'POWER': '£energy_texticon §YElectric Power§!',
 'MACH': '£mil_factory §YMachinery and Munitions§!',
 'PLAN': '£industry_texticon §YTotal plan fulfilment§!'}

POL_T_EXTRA = ['Kwantung Army patience',
 'Hsinking Bureaucracy',
 'Resting level',
 'The Mantetsu Question',
 'Mantetsu Question',
 'Convene the Joint Council',
 'Issue an Internal Guidance Directive',
 'Kwantung Army',
 'Tokyo']

SEC_T = ['Banditry growth',
 'weekly banditry growth',
 'Average banditry',
 'Banditry',
 'banditry',
 'Route Army',
 'Route Armies',
 'First Route Army',
 'Second Route Army',
 'Third Route Army',
 'grievance',
 'Punitive Sweeps',
 'Punitive Sweep',
 'Three-Year Public Security Plan',
 'The Three-Year Public Security Plan',
 'The Nozoe Punitive Campaign',
 'Public Security']


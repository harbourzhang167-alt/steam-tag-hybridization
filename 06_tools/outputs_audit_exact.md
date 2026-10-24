```
==============================================================================
A. games_clustered_meta_export.csv  (FULL POPULATION)
==============================================================================
shape                : (17686, 15)   (expect (17686, 15))
columns              : ['appid', 'name', 'Release_Year', 'Clean_Priority_Tags', 'Meta_Tags', 'Game_Cluster', 'in_focus_cluster', 'Total_Reviews', 'positive', 'negative', 'price', 'Hybridization_Index', 'Log_Reviews', 'Hybrid_Centered', 'Hybrid_Centered_Squared']

dtypes:
appid                        int64
name                           str
Release_Year                 int64
Clean_Priority_Tags            str
Meta_Tags                      str
Game_Cluster                 int64
in_focus_cluster             int64
Total_Reviews                int64
positive                     int64
negative                     int64
price                      float64
Hybridization_Index          int64
Log_Reviews                float64
Hybrid_Centered            float64
Hybrid_Centered_Squared    float64

describe() of key numeric columns:
                           count          mean           std         min         25%         50%          75%           max
price                    17686.0  1.159607e+01     11.964447    0.000000    2.090000    9.590000    17.990000  2.699900e+02
Total_Reviews            17686.0  3.928852e+03  23851.816823  100.000000  179.000000  396.000000  1364.750000  1.195980e+06
Hybridization_Index      17686.0  9.324664e+00      3.675560    0.000000    7.000000   10.000000    12.000000  2.000000e+01
Log_Reviews              17686.0  6.399836e+00      1.529153    4.615121    5.192957    5.983936     7.219459  1.399448e+01
Hybrid_Centered          17686.0  6.685192e-16      3.675560   -9.324664   -2.324664    0.675336     2.675336  1.067534e+01
Hybrid_Centered_Squared  17686.0  1.350898e+01     15.306292    0.105406    1.754734    7.157425    21.858771  1.139628e+02

describe() rounded, as reported by the notebook:
       Hybridization_Index  Hybrid_Centered
count             17686.00         17686.00
mean                  9.32             0.00
std                   3.68             3.68
min                   0.00            -9.32
25%                   7.00            -2.32
50%                  10.00             0.68
75%                  12.00             2.68
max                  20.00            10.68

-- Release_Year distribution --
 year    n  share_pct
 2015 1473      8.329
 2016 1922     10.867
 2017 1904     10.766
 2018 1850     10.460
 2019 1526      8.628
 2020 1901     10.749
 2021 1628      9.205
 2022 1395      7.888
 2023 1650      9.329
 2024 2129     12.038
 2025  308      1.741

-- Game_Cluster distribution --
 cluster    n  share_pct
       0 2181      12.33
       1 2163      12.23
       2 1741       9.84
       3 1341       7.58
       4 2478      14.01
       5 2620      14.81
       6 1977      11.18
       7 3185      18.01
Game_Cluster dtype   : int64
in_focus_cluster vc  : {1: 17686}

price == 0           : 2347 rows  (13.2704 %)
price <  0           : 0 rows
price isna           : 0 rows
price >= 100         : 1 rows
price max            : 269.99
price >= 100 rows:
 appid          name  Release_Year  price  Total_Reviews  Game_Cluster
502570 Houdini Indie          2018 269.99            241             5
top 15 price rows:
  appid                             name  price  Total_Reviews
 502570                    Houdini Indie 269.99            241
 904960                      Cine Tracer  89.99            458
 837510              Pixel Game Maker MV  84.99            563
1076160       Command: Modern Operations  79.99           1396
 370540   Gary Grigsby's War in the East  79.99            568
1775550 Gary Grigsby's War in the East 2  79.99            362
 644710   Gary Grigsby's War in the West  79.99            169
 363890                     RPG Maker MV  79.99           8162
1096900                     RPG Maker MZ  79.99           1798
 347400   001 Game Creator: 2024 Edition  79.99            294
1716740                        Starfield  69.99         163967
1222680             Need for Speed™ Heat  69.99         128521
2246340             Monster Hunter Wilds  69.99         132740
2054970                 Dragon's Dogma 2  69.99         105233
1774580        STAR WARS Jedi: Survivor™  69.99          62413

Hybridization_Index == 0 : 16 rows
regression N (HI > 0)    : 17670   (expect 17670)
full N                   : 17686   (expect 17686)
implied drop             : 16
rows dropped from the regression (HI == 0):
  appid                                        name  Release_Year Meta_Tags  Game_Cluster  Total_Reviews  price
 477130                                       Surge          2016       NaN             5            266   0.00
 976410                           Infinite Children          2019       NaN             5            135   0.00
 607440                                  Escape: VR          2017       NaN             5            174   1.99
 920490                    Driver Booster for Steam          2018       NaN             5           8873   0.00
 382110                     Virtual Desktop Classic          2016       NaN             5           2049  14.99
1787090                                MyDockFinder          2021       NaN             5           5263   4.99
1009850                       OVR Advanced Settings          2020       NaN             5           4396   7.99
 672870                                  ScreenPlay          2021       NaN             5           1266   0.00
 367670                        Controller Companion          2015       NaN             5           2573   2.99
1114420                     PLAY'A VR  Video Player          2019       NaN             5            275   0.00
1494460                                    Desktop+          2021       NaN             5            636   0.00
 992490                     iVRy Driver for SteamVR          2019       NaN             5            380   0.00
 337070 Dimmdrive :: Gaming Ramdrive @ 10,000+ MB/s          2015       NaN             5            445  14.99
 586210                                     OVRdrop          2017       NaN             5            528   9.99
 464170                                      VRMark          2016       NaN             5            142  19.99
1022230                            Magic Borderless          2019       NaN             5            146   2.99
their cluster membership:
Game_Cluster
5    16

-- Pearson correlation matrix --
                        price  Hybridization_Index  Log_Reviews  Total_Reviews
price                1.000000             0.165018     0.307984       0.120322
Hybridization_Index  0.165018             1.000000     0.211357       0.050578
Log_Reviews          0.307984             0.211357     1.000000       0.442648
Total_Reviews        0.120322             0.050578     0.442648       1.000000

Spearman (robustness):
                        price  Hybridization_Index  Log_Reviews  Total_Reviews
price                1.000000             0.200469     0.240638       0.240638
Hybridization_Index  0.200469             1.000000     0.184874       0.184874
Log_Reviews          0.240638             0.184874     1.000000       1.000000
Total_Reviews        0.240638             0.184874     1.000000       1.000000

-- mean / median of Log_Reviews and price by Game_Cluster --
                 n  n_HI_gt0  LogRev_mean  LogRev_median  price_mean  price_median    HI_mean
Game_Cluster                                                                                 
0             2181      2181     5.770596       5.455321    5.659037          2.99   6.327831
1             2163      2163     6.392816       6.003887   10.868729          9.37  11.968100
2             1741      1741     6.338494       5.953243    9.949747          7.99  11.786904
3             1341      1341     6.500131       6.167516   15.776271         14.99  11.151380
4             2478      2478     6.638292       6.226535   14.625472         11.99   7.487086
5             2620      2604     6.213367       5.866468    9.834557          5.99   6.711069
6             1977      1977     6.962956       6.549651   15.797466         14.99  11.642893
7             3185      3185     6.445118       6.011267   11.779636          9.99   9.607221

mean(Hybridization_Index)      : np.float64(9.3246635757096)   (notebook prints 9.32)
median(Hybridization_Index)    : 10.0
std(Hybridization_Index)       : np.float64(3.6755600509002115)
max|Hybrid_Centered - (HI - mean)|      : np.float64(2.220446049250313e-16)   (tolerance 1e-6 -> PASS)
max|Hybrid_Centered_Squared - HC^2|     : np.float64(1.7763568394002505e-15)   (tolerance 1e-6 -> PASS)
implied centering constant     : min=np.float64(9.3246635757096) max=np.float64(9.3246635757096)
max|Log_Reviews - log1p(Total_Reviews)| : np.float64(1.7763568394002505e-15)   (tolerance 1e-9 -> PASS)
max|Log_Reviews - ln(Total_Reviews)|    : np.float64(0.009950330853167877)   (for reference)
max|Total_Reviews - (positive+negative)|: np.int64(0)

distinct appid        : 17686
rows with duplicated appid : 0
exact duplicate rows (all cols) : 0
duplicated (appid, name) pairs  : 0

==============================================================================
B. cluster_megatag_reference.csv + cluster_cohens_h_tags.csv
==============================================================================
cluster_megatag_reference.csv (full):
 cluster_id  n_games  share_pct                                                     defining_meta_tags  mean_hybrid_index  median_hybrid_index  min_hybrid_index  max_hybrid_index
          0     2181      12.33          Casual; Adventure/Narrative; Action; Puzzle/Board; Simulation              6.328                  6.0                 1                16
          1     2163      12.23 Adventure/Narrative; Story-Driven; Perspective; Mood (Dark); Art Style             11.968                 12.0                 5                18
          2     1741       9.84            Mood (Positive); Casual; Simulation; Perspective; Art Style             11.787                 12.0                 5                20
          3     1341       7.58             RPG; Strategy; Perspective; Adventure/Narrative; Art Style             11.151                 12.0                 2                17
          4     2478      14.01          Simulation; Strategy; Perspective; Core System; Sports/Racing              7.487                  8.0                 1                17
          5     2620      14.81                     Adventure/Narrative; RPG; Art Style; Adult; Action              6.711                  6.0                 0                17
          6     1977      11.18             Action; Core System; Perspective; Adventure/Narrative; RPG             11.643                 12.0                 4                19
          7     3185      18.01                    Action; Perspective; Art Style; Shooter; Platformer              9.607                 10.0                 1                18

n_games sum   : 17686   (expect 17686)
share_pct sum : 99.99000000000001   (expect ~100)
max |share_pct - n_games/17686*100| : 0.003977 pp

cluster size cross-check (reference vs export):
   ref_n_games  export_n  diff
0         2181      2181     0
1         2163      2163     0
2         1741      1741     0
3         1341      1341     0
4         2478      2478     0
5         2620      2620     0
6         1977      1977     0
7         3185      3185     0

cluster_cohens_h_tags.csv (full):
 cluster_id                meta_tag  cohens_h  share_in_cluster  share_global
          0                  Casual    1.8316            1.0000        0.3711
          0            Puzzle/Board    0.2757            0.3796        0.2521
          0                 Clicker    0.1125            0.0431        0.0232
          0                   Party    0.0998            0.0197        0.0083
          0                   Short    0.0861            0.0541        0.0363
          1            Story-Driven    1.4119            0.9223        0.3026
          1     Adventure/Narrative    1.1059            0.9783        0.5841
          1             Atmospheric    0.8858            0.6773        0.2501
          1             Mood (Dark)    0.7845            0.6186        0.2408
          1            Puzzle/Board    0.6837            0.5821        0.2521
          2         Mood (Positive)    1.3409            0.9242        0.3389
          2                  Casual    1.0543            0.8564        0.3711
          2              Simulation    0.7289            0.7111        0.3555
          2                Colorful    0.6970            0.4446        0.1385
          2             Perspective    0.5394            0.8742        0.6507
          3                     RPG    1.5246            0.9433        0.2895
          3                Strategy    1.2744            0.8516        0.2627
          3       Turn-Based Combat    1.0799            0.4817        0.0507
          3              Turn-Based    0.9216            0.4057        0.0518
          3           Fantasy/Magic    0.7848            0.5667        0.1970
          4              Simulation    1.1372            0.8737        0.3555
          4                Strategy    0.9982            0.7413        0.2627
          4         Military/Combat    0.3825            0.2046        0.0754
          4                Tactical    0.3585            0.1667        0.0571
          4           Sports/Racing    0.3474            0.2103        0.0888
          5     Adventure/Narrative    0.6401            0.8618        0.5841
          5                   Adult    0.4815            0.3008        0.1110
          5                RPGMaker    0.3325            0.1008        0.0244
          5      Female Protagonist    0.2461            0.2363        0.1407
          5                     RPG    0.1570            0.3630        0.2895
          6             Core System    1.2652            0.8821        0.3075
          6                  Action    1.0681            0.9191        0.4629
          6                     RPG    0.7765            0.6677        0.2895
          6             Perspective    0.6480            0.9079        0.6507
          6             Exploration    0.5411            0.4234        0.1798
          7                  Action    1.4442            0.9900        0.4629
          7                 Shooter    0.6941            0.4631        0.1527
          7                  Arcade    0.5626            0.3206        0.0993
          7 Arcade/Top-Down Shooter    0.5081            0.2396        0.0648
          7        Fighting/Brawler    0.3784            0.2446        0.1039

rows: 40  clusters: [np.int64(0), np.int64(1), np.int64(2), np.int64(3), np.int64(4), np.int64(5), np.int64(6), np.int64(7)]
tags per cluster: {0: 5, 1: 5, 2: 5, 3: 5, 4: 5, 5: 5, 6: 5, 7: 5}

meta tags with Cohen's h >= 0.5, per cluster:
  cluster 0 (1): Casual (1.8316)
  cluster 1 (5): Story-Driven (1.4119), Adventure/Narrative (1.1059), Atmospheric (0.8858), Mood (Dark) (0.7845), Puzzle/Board (0.6837)
  cluster 2 (5): Mood (Positive) (1.3409), Casual (1.0543), Simulation (0.7289), Colorful (0.697), Perspective (0.5394)
  cluster 3 (5): RPG (1.5246), Strategy (1.2744), Turn-Based Combat (1.0799), Turn-Based (0.9216), Fantasy/Magic (0.7848)
  cluster 4 (2): Simulation (1.1372), Strategy (0.9982)
  cluster 5 (1): Adventure/Narrative (0.6401)
  cluster 6 (5): Core System (1.2652), Action (1.0681), RPG (0.7765), Perspective (0.648), Exploration (0.5411)
  cluster 7 (4): Action (1.4442), Shooter (0.6941), Arcade (0.5626), Arcade/Top-Down Shooter (0.5081)

clusters with fewer than 5 tags at h >= 0.5 : [] / counts {0: 1, 1: 5, 2: 5, 3: 5, 4: 2, 5: 1, 6: 5, 7: 4}

share_global consistency across clusters (same tag must have identical share_global):
  tags with inconsistent share_global: 0  []

overlap between reference defining_meta_tags (top-5) and Cohen's h >= 0.5 list:
  cluster 0: reference=['Casual', 'Adventure/Narrative', 'Action', 'Puzzle/Board', 'Simulation']
             cohens>=0.5=['Casual']
             shared=['Casual']  ref_only=['Action', 'Adventure/Narrative', 'Puzzle/Board', 'Simulation']  cohens_only=[]
  cluster 1: reference=['Adventure/Narrative', 'Story-Driven', 'Perspective', 'Mood (Dark)', 'Art Style']
             cohens>=0.5=['Story-Driven', 'Adventure/Narrative', 'Atmospheric', 'Mood (Dark)', 'Puzzle/Board']
             shared=['Adventure/Narrative', 'Mood (Dark)', 'Story-Driven']  ref_only=['Art Style', 'Perspective']  cohens_only=['Atmospheric', 'Puzzle/Board']
  cluster 2: reference=['Mood (Positive)', 'Casual', 'Simulation', 'Perspective', 'Art Style']
             cohens>=0.5=['Mood (Positive)', 'Casual', 'Simulation', 'Colorful', 'Perspective']
             shared=['Casual', 'Mood (Positive)', 'Perspective', 'Simulation']  ref_only=['Art Style']  cohens_only=['Colorful']
  cluster 3: reference=['RPG', 'Strategy', 'Perspective', 'Adventure/Narrative', 'Art Style']
             cohens>=0.5=['RPG', 'Strategy', 'Turn-Based Combat', 'Turn-Based', 'Fantasy/Magic']
             shared=['RPG', 'Strategy']  ref_only=['Adventure/Narrative', 'Art Style', 'Perspective']  cohens_only=['Fantasy/Magic', 'Turn-Based', 'Turn-Based Combat']
  cluster 4: reference=['Simulation', 'Strategy', 'Perspective', 'Core System', 'Sports/Racing']
             cohens>=0.5=['Simulation', 'Strategy']
             shared=['Simulation', 'Strategy']  ref_only=['Core System', 'Perspective', 'Sports/Racing']  cohens_only=[]
  cluster 5: reference=['Adventure/Narrative', 'RPG', 'Art Style', 'Adult', 'Action']
             cohens>=0.5=['Adventure/Narrative']
             shared=['Adventure/Narrative']  ref_only=['Action', 'Adult', 'Art Style', 'RPG']  cohens_only=[]
  cluster 6: reference=['Action', 'Core System', 'Perspective', 'Adventure/Narrative', 'RPG']
             cohens>=0.5=['Core System', 'Action', 'RPG', 'Perspective', 'Exploration']
             shared=['Action', 'Core System', 'Perspective', 'RPG']  ref_only=['Adventure/Narrative']  cohens_only=['Exploration']
  cluster 7: reference=['Action', 'Perspective', 'Art Style', 'Shooter', 'Platformer']
             cohens>=0.5=['Action', 'Shooter', 'Arcade', 'Arcade/Top-Down Shooter']
             shared=['Action', 'Shooter']  ref_only=['Art Style', 'Perspective', 'Platformer']  cohens_only=['Arcade', 'Arcade/Top-Down Shooter']

==============================================================================
C. all_tags.txt
==============================================================================
lines (non-empty, trailing newline stripped) : 448
empty / whitespace-only lines : 0
blank ('' after strip)        : 0
distinct values               : 448
duplicates                    : 0  []
lines with leading/trailing whitespace : 0
is strictly ascending sorted  : True
is the sorted(set()) of itself: True

==============================================================================
D. Meta_Tags vocabulary / Hybridization_Index integrity
==============================================================================
distinct meta-tag labels in Meta_Tags : 192

all distinct meta-tag labels with frequency (sorted desc):
                            label  n_games  share_pct
                      Perspective    11509     65.074
              Adventure/Narrative    10330     58.408
                        Art Style     8800     49.757
                           Action     8187     46.291
                           Casual     6563     37.108
                       Simulation     6288     35.554
                  Mood (Positive)     5994     33.891
                      Core System     5438     30.747
                     Story-Driven     5351     30.256
                              RPG     5120     28.949
                         Strategy     4646     26.269
                     Puzzle/Board     4458     25.206
                      Atmospheric     4424     25.014
                      Mood (Dark)     4258     24.076
                    Fantasy/Magic     3485     19.705
                      Exploration     3180     17.980
                 Sci-Fi/Cyberpunk     2901     16.403
                          Shooter     2700     15.266
                       Platformer     2554     14.441
               Female Protagonist     2489     14.073
                         Colorful     2450     13.853
                            Adult     1964     11.105
                        Difficult     1913     10.816
                     Other Themes     1885     10.658
                       Historical     1885     10.658
                 Fighting/Brawler     1837     10.387
                           Arcade     1756      9.929
                        Roguelike     1641      9.279
                    Sports/Racing     1571      8.883
                          Violent     1562      8.832
                  Military/Combat     1333      7.537
                         Stylized     1327      7.503
          Character Customization     1270      7.181
                           Combat     1199      6.779
          Arcade/Top-Down Shooter     1146      6.480
                          Physics     1106      6.254
                         Tactical     1010      5.711
                         Cartoony     1003      5.671
                    Side Scroller      934      5.281
                       Turn-Based      917      5.185
                Turn-Based Combat      897      5.072
                    Immersive Sim      857      4.846
                        Emotional      776      4.388
                          Surreal      734      4.150
                       Old School      647      3.658
                            Short      642      3.630
                           Linear      637      3.602
                          Cartoon      616      3.483
                       Dark Humor      571      3.229
                           1990's      567      3.206
                        Cinematic      541      3.059
                       Fast-Paced      540      3.053
                        Narration      493      2.788
                    Psychological      461      2.607
                           Nature      440      2.488
                         RPGMaker      431      2.437
                        Education      426      2.409
                          Clicker      410      2.318
                      Competitive      380      2.149
                     Conversation      356      2.013
                       Team-Based      355      2.007
                     Score Attack      346      1.956
                            Idler      333      1.883
                     Level Editor      328      1.855
                            1980s      319      1.804
                      Psychedelic      315      1.781
                         Abstract      315      1.781
                      Destruction      306      1.730
                       Dystopian       306      1.730
                     Experimental      304      1.719
                       Comic Book      297      1.679
                           Flight      297      1.679
                        Nonlinear      289      1.634
                     Collectathon      282      1.594
                             Cats      268      1.515
                           Modern      253      1.431
                      Dark Comedy      246      1.391
          Artificial Intelligence      230      1.300
                       Capitalism      224      1.267
                           Rhythm      222      1.255
                             Noir      209      1.182
               Creature Collector      205      1.159
                          Trading      198      1.120
                    Philosophical      198      1.120
                     Split Screen      197      1.114
                          Science      191      1.080
                         Tutorial      190      1.074
                          Cooking      189      1.069
                        Political      183      1.035
                           Remake      181      1.023
                   Co-op Campaign      179      1.012
                          Parody       171      0.967
                              FMV      170      0.961
                        Narrative      155      0.876
            Design & Illustration      154      0.871
                Gun Customization      150      0.848
                      Class-Based      150      0.848
                        Real-Time      148      0.837
                          Fishing      147      0.831
                            Party      146      0.826
                          America      145      0.820
              Grid-Based Movement      145      0.820
                          Hacking      142      0.803
                     Cult Classic      142      0.803
                         Politics      141      0.797
                         Hex Grid      135      0.763
                           Satire      135      0.763
              Villain Protagonist      132      0.746
                           Mining      131      0.741
                       Illuminati      130      0.735
                        Diplomacy      129      0.729
             Real-Time with Pause      129      0.729
                      Bullet Time      129      0.729
                    Battle Royale      122      0.690
                              Dog      121      0.684
                           Trains      119      0.673
                        Dinosaurs      117      0.662
                      Time Travel      117      0.662
                       Conspiracy      115      0.650
                            Faith      114      0.645
                      Programming      114      0.645
                          Hunting      111      0.628
                Dynamic Narration      108      0.611
                       Underwater      107      0.605
                Time Manipulation      107      0.605
                      Kickstarter      101      0.571
                        Immersive      100      0.565
                             6DOF       97      0.548
                           Sequel       90      0.509
                       Action RTS       85      0.481
                      Underground       84      0.475
                        Superhero       83      0.469
                   Touch-Friendly       81      0.458
                        Minigames       76      0.430
                Quick-Time Events       75      0.424
                           Typing       73      0.413
                         Episodic       72      0.407
                       Experience       72      0.407
                        Nostalgia       72      0.407
                          Foreign       64      0.362
             Animation & Modeling       64      0.362
                      Time Attack       63      0.356
                         Gambling       60      0.339
                             Snow       60      0.339
                            Dwarf       57      0.322
                           Horses       55      0.311
                            Bikes       54      0.305
                 Social Deduction       49      0.277
                   Games Workshop       49      0.277
                        GameMaker       49      0.277
                             Mars       49      0.277
                          Archery       45      0.254
Music-Based Procedural Generation       43      0.243
                       Werewolves       42      0.237
                        Submarine       38      0.215
                      Unforgiving       37      0.209
                 Video Production       36      0.204
                              Jet       34      0.192
               Silent Protagonist       34      0.192
               Dungeons & Dragons       32      0.181
                             LEGO       31      0.175
                    Warhammer 40K       30      0.170
                       Jump Scare       28      0.158
                 Audio Production       28      0.158
                       Spaceships       27      0.153
                    Photo Editing       26      0.147
                Software Training       21      0.119
                   Web Publishing       21      0.119
   Intentionally Awkward Controls       19      0.107
                             Pool       19      0.107
                 Based On A Novel       19      0.107
                           Gaming       17      0.096
                     Well-Written       17      0.096
                 Electronic Music       16      0.090
                      Shop Keeper       15      0.085
                          TrackIR       11      0.062
                    Voice Control       11      0.062
                         Hardware       10      0.057
                         Lemmings       10      0.057
                          Ambient        9      0.051
                              Fox        9      0.051
                       Rock Music        8      0.045
               Instrumental Music        8      0.045
                       Electronic        8      0.045
                           Coding        7      0.040
                            Birds        7      0.040
                    Steam Machine        6      0.034
                       Lara Croft        4      0.023
                           Reboot        3      0.017
                     Feature Film        3      0.017
                              Elf        2      0.011
                          VR Only        2      0.011

labels that are canonical META_DICT values : 26
labels NOT in META_DICT (raw Steam tags that fell through) : 166
  ['1980s', "1990's", '6DOF', 'Abstract', 'Action RTS', 'Ambient', 'America', 'Animation & Modeling', 'Arcade', 'Archery', 'Artificial Intelligence', 'Atmospheric', 'Audio Production', 'Based On A Novel', 'Battle Royale', 'Bikes', 'Birds', 'Bullet Time', 'Capitalism', 'Cartoon', 'Cartoony', 'Cats', 'Character Customization', 'Cinematic', 'Class-Based', 'Clicker', 'Co-op Campaign', 'Coding', 'Collectathon', 'Colorful', 'Combat', 'Comic Book', 'Competitive', 'Conspiracy', 'Conversation', 'Cooking', 'Creature Collector', 'Cult Classic', 'Dark Comedy', 'Dark Humor', 'Design & Illustration', 'Destruction', 'Difficult', 'Dinosaurs', 'Diplomacy', 'Dog', 'Dungeons & Dragons', 'Dwarf', 'Dynamic Narration', 'Dystopian ', 'Education', 'Electronic', 'Electronic Music', 'Elf', 'Emotional', 'Episodic', 'Experience', 'Experimental', 'Exploration', 'FMV', 'Faith', 'Fast-Paced', 'Feature Film', 'Female Protagonist', 'Fishing', 'Flight', 'Foreign', 'Fox', 'Gambling', 'GameMaker', 'Games Workshop', 'Gaming', 'Grid-Based Movement', 'Gun Customization', 'Hacking', 'Hardware', 'Hex Grid', 'Horses', 'Hunting', 'Idler', 'Illuminati', 'Immersive', 'Immersive Sim', 'Instrumental Music', 'Intentionally Awkward Controls', 'Jet', 'Jump Scare', 'Kickstarter', 'LEGO', 'Lara Croft', 'Lemmings', 'Level Editor', 'Linear', 'Mars', 'Minigames', 'Mining', 'Modern', 'Music-Based Procedural Generation', 'Narration', 'Narrative', 'Nature', 'Noir', 'Nonlinear', 'Nostalgia', 'Old School', 'Parody ', 'Philosophical', 'Photo Editing', 'Physics', 'Political', 'Politics', 'Pool', 'Programming', 'Psychedelic', 'Psychological', 'Quick-Time Events', 'RPGMaker', 'Real-Time', 'Real-Time with Pause', 'Reboot', 'Remake', 'Rhythm', 'Rock Music', 'Satire', 'Science', 'Score Attack', 'Sequel', 'Shop Keeper', 'Short', 'Side Scroller', 'Silent Protagonist', 'Snow', 'Social Deduction', 'Software Training', 'Spaceships', 'Split Screen', 'Steam Machine', 'Stylized', 'Submarine', 'Superhero', 'Surreal', 'Tactical', 'Team-Based', 'Time Attack', 'Time Manipulation', 'Time Travel', 'Touch-Friendly', 'TrackIR', 'Trading', 'Trains', 'Turn-Based', 'Turn-Based Combat', 'Tutorial', 'Typing', 'Underground', 'Underwater', 'Unforgiving', 'VR Only', 'Video Production', 'Villain Protagonist', 'Violent', 'Voice Control', 'Warhammer 40K', 'Web Publishing', 'Well-Written', 'Werewolves']
canonical META_DICT values never observed in the export : []
'IGNORE' present in Meta_Tags : False  (n=0)

labels with leading/trailing whitespace (bypass META_DICT) : 2
  'Dystopian '  n_games=306
  'Parody '  n_games=171
games carrying >=1 whitespace-contaminated label : 471 / 17686 (2.66 %)

games whose Meta_Tags contain at least one unmapped raw tag : 15117 / 17686

distinct meta tags per game:
  min=0  max=20  mean=np.float64(9.3246635757096)  median=10.0  std=np.float64(3.6755600509002115)
  max|Hybridization_Index - len(Meta_Tags)| : 0
  distribution:
Meta_Tags
0       16
1      164
2      560
3      822
4      931
5      894
6      937
7      969
8     1197
9     1516
10    1867
11    2034
12    2105
13    1680
14    1113
15     567
16     240
17      59
18      13
19       1
20       1

top 20 most frequent meta tags:
Perspective            11509
Adventure/Narrative    10330
Art Style               8800
Action                  8187
Casual                  6563
Simulation              6288
Mood (Positive)         5994
Core System             5438
Story-Driven            5351
RPG                     5120
Strategy                4646
Puzzle/Board            4458
Atmospheric             4424
Mood (Dark)             4258
Fantasy/Magic           3485
Exploration             3180
Sci-Fi/Cyberpunk        2901
Shooter                 2700
Platformer              2554
Female Protagonist      2489

---- end of full-population audit ----
```

import json,re,os
posts=json.load(open('/tmp/posts_idx.json'))
def res(prefix):
    if prefix in posts: return prefix
    m=sorted((s for s in posts if s.startswith(prefix)),key=len)
    if not m: print("MISSING",prefix); return None
    if len(m)>1: print("MULTI",prefix,m[:3])
    return m[0]
H=[
("vegetarian-indian-recipes","Vegetarian Indian Recipes: Dals, Curries and Sides","Lentils, chickpeas, potatoes and greens, built up with whole spices",
 "Vegetarian Indian recipes from Herbivoracious: dal, chana masala, saag, gobi masala, potato sides and more. Many are vegan, and most come together in under an hour.",
 "Indian-style cooking is a natural fit for vegetarians: lentils, chickpeas, cauliflower, potatoes and greens, all built up with whole spices and fresh aromatics. These are the Indian and Indian-style recipes on Herbivoracious, from a five-minute cabbage side dish to dals and curries that simmer while you do something else.\n\nIf you are new to this kind of cooking, start with the quick chana masala with mushrooms or the five-minute cabbage. Both are short, simple recipes.",
 ["kala-chana-black-chickpea-curry","quick-chana-mushroom-masala-chickpea-curry-recipe","indian-lentil-soup-with-fenugreek","five-minute-ind","potatoes-with-crispy-curry-leaves-recipe","recipe-urad-dal","chana-dal-in-the-style-of-puri","saag-with-collard-greens-kale-and-spinach-recipe","gobi-masala-cauliflower-curry-recipe","aloo-tikki-indian-potato-fritters-recipe","beet-curry-recipe-1","spicy-and-seedy-indian-potatoes-recipe","recipe-chana-ch","cucumber-radish-and-cilantro-raita-recipe"]),
("vegetarian-mexican-recipes","Vegetarian Mexican Recipes","Tacos, enchiladas, salsas and beans, no meat required",
 "Vegetarian Mexican recipes from Herbivoracious: crispy quesadillas, chilaquiles verdes, enchiladas, tamales, salsas, frijoles charros and more.",
 "Mexican food is full of dishes that never needed meat to begin with: beans, tortillas, chiles, salsas, eggs and masa. These are the Mexican and Latin-inspired recipes on Herbivoracious, from a weekend batch of tamales to a quick quesadilla.\n\nThe salsas and the red chile sauce are good places to start, because they improve almost everything else on the table.",
 ["quesadilla","chilaquiles-verde-mexican","austin-style-breakfast-tacos-recipe","vegetarian-frijoles-charros","enchiladas-de-mole-recipe","swiss-chard-enchiladas","chanterelle-tostadas-recipes","grilled-tofu-and-pepper-vegetarian-tacos-recipe","achiote-rubbed","red-chili-sauce-for-tamales","nuevo-leon-style-tamales","vegetarian-pozole-de-frijol","coconut-rice-with-black-beans","avocado-and-tomatillo-salsa-recipe","ridiculously-good-guacamole-recipe","chile-con-limon"]),
("vegetarian-bean-and-lentil-recipes","Bean and Lentil Recipes: Soups, Stews, Salads and Mains","Beans and lentils as the main event",
 "Vegetarian bean and lentil recipes from Herbivoracious: black bean soup, ful medames, mujadara, red lentil soup, chili and more. Hearty, budget-friendly and mostly vegan.",
 "Dried beans and lentils are cheap, filling and endlessly adaptable. These recipes treat them as the main event: soups, stews, salads and pilafs from Ethiopia, Syria, Mexico, India and beyond.\n\nDried beans and lentils are also among the most affordable ingredients you can buy.",
 ["ethiopian-ful-mudammas-recipe","black-bean-soup-recipe","black-bean-soup-with-orange-jalapeno-salsa-recipe","recipe-mujadara","recipe-syrian-y","indian-lentil-soup-with-fenugreek","vegetarian-frijoles-charros","coconut-rice-with-black-beans","whole-bean-ful-medames","recipe-cranberr","caviar-lentil-salad","spanish-lentil-and-mushroom-stew-recipe","lentil-and-cucumber-salad","red-lentil-and-kabocha","recipe-veggie-c","white-bean-and-kale-soup-recipe"]),
("vegetarian-mushroom-recipes","Mushroom Recipes: Shiitake, Maitake, Chanterelle and More","From everyday shiitakes to seasonal wild mushrooms",
 "Vegetarian mushroom recipes from Herbivoracious: kinoko gohan, maitake, king oyster, chanterelles, shiitake, porcini and more.",
 "Mushrooms bring the savory, meaty depth that vegetarian cooking sometimes needs. These recipes cover everyday cultivated mushrooms such as shiitake, king oyster and maitake, plus seasonal wild chanterelles, morels and porcini.\n\nBrowning them properly in the pan is where most of the flavor comes from.",
 ["kinoko-gohan-japanese-mushroom-rice-recipe","vegan-bacon-from-king-oyster","beer-battered-maitake","maitake-mushrooms-in-smoky-tea-broth","hongos-en-escabeche","chanterelle-tostadas-recipes","potatoes-chanterelles-shallots","porcini-cepes-mushroom-crudo","shiitake-and-morel-ravioli","gorditas-with-roasted-mushrooms","maple-roasted-shiitake-mushrooms-recipe","king-oyster-mushroom-lettuce-wraps","quick-chana-mushroom-masala","kimchi-stew-kimchi-jigae","strata-with-caramelized-onions","spanish-lentil-and-mushroom-stew-recipe"]),
("vegetarian-korean-recipes","Vegetarian Korean Recipes: Kimchi, Bibimbap, Mandu and More","Korean flavors, no meat or fish",
 "Vegetarian Korean recipes from Herbivoracious: kimchi fried rice, bibimbap, mandu, banchan, kimchi jigae, bibim naengmyeon and homemade kimchi.",
 "Korean cooking leans on fermented, spicy and savory flavors that translate well to vegetarian food. These recipes include kimchi fried rice, bibimbap, mandu dumplings, cold spicy noodles and the small side dishes known as banchan.\n\nIf you want to make your own kimchi, the full recipe covers fermenting napa cabbage at home, and the green apple version is a fast pickle in the same spirit.",
 ["kimchi-fried-rice-kimchi-bokkeumbap-recipe","vegetarian-bibimbap","mandu-koreanstyle","bibim-naegnmyeon","three-easy-banchan","kimchi-stew-kimchi-jigae","quick-green-apple-kimchi-recipe","making-your-own-kimchi-recipe","tofu-and-kimchi-dinner-for-one","crispy-soba-buckwheat","recipe-soft-boi","dduk-gogi"]),
("vegetarian-tofu-recipes","Tofu Recipes: Crispy, Saucy and Full of Flavor","Tofu dishes that go well beyond a stir-fry",
 "Vegetarian tofu recipes from Herbivoracious: Sichuan green beans, banh mi chay, Mission Chinese-style tofu, tacos, curry and more.",
 "Good tofu cooking is about texture and sauce. These recipes use firm tofu, pressed and seared or fried until it has a real crust, then paired with bold sauces from Sichuan, Vietnam, Thailand and Mexico.\n\nSeveral of these use pressed tofu, which holds its shape and browns better in the pan.",
 ["mission-chinese-style-tofu","asparagus-and-tofu-with-guilin","recipe-vietname","vietnamese-cabbage-and-herb-salad","grilled-tofu-and-pepper-vegetarian-tacos-recipe","sichuan-dry-fried-green-beans-and-tofu","red-curry-delicata-squash-and-tofu","aromatic-tofu-en-papillote","pan-seared-pressed-tofu","caramel-cooked-tofu-recipe","super-spicy-tofu","tofu-and-kimchi-dinner-for-one","soba-in-shoyu-broth-with-asparagus","tofu-dengaku-recipe","seared-tofu-poke"]),
("vegetarian-chickpea-recipes","Chickpea Recipes: Curries, Stews, Fritters and Salads","One humble bean, many different dinners",
 "Vegetarian chickpea recipes from Herbivoracious: kala chana, chana masala, Turkish chickpea and potato stew, tagines, chickpea cakes and more.",
 "Chickpeas are one of the most useful ingredients in a vegetarian kitchen: they are filling, they take on spices well, and they work in soups, stews, salads and fritters. These recipes range from an Indian black chickpea curry to Turkish and Moroccan stews, with a ten-minute salad for nights when you need something fast.",
 ["kala-chana-black-chickpea-curry","quick-chana-mushroom-masala-chickpea-curry-recipe","chickpea-and-potato-stew-with-baharat","zucchini-chickpea-tagine","chickpea-and-green-olive-tagine","saffron-chickpea-stew-with-grilled-porcini","chickpea-cakes-recipe","chickpea-fritters-recipe","chickpea-and-saffron-pilaf","chickpea-spinach-and-tomato-soup","farro-and-chickpea-soup","ten-minute-chickpea-salad","chana-dal-in-the-style-of-puri","recipe-chana-ch"]),
("vegetarian-eggplant-recipes","Eggplant Recipes: Curries, Pastas, Parmesan and More","Eggplant from Thai basil stir-fry to eggplant parmigiana",
 "Vegetarian eggplant recipes from Herbivoracious: Thai basil eggplant, coconut curry, sabich, eggplant parmigiana, chermoula-stuffed eggplant and more.",
 "Eggplant can be silky, creamy, smoky or crisp depending on how you cook it. These recipes show the range: a fast Thai basil stir-fry, a coconut milk curry, an Iraqi-Jewish sabich sandwich, a classic parmigiana, and a stuffed eggplant with chermoula.",
 ["thai-basil-eggplant-recipe","eggplant-kaffir-lime-coconut-milk-curry-recipe","tiny-eggplant-and-okra","recipe-sabich","eggplant-parmes","over-the-top-eggplant-parmigiana","pappardelle-with-eggplant-ragu","grilled-eggplant-with-arrabiata-fresca","easy-eggplant-and-ricotta-rolls","chermoula-stuffed-eggplant","persian-italian-eggplant-stew","tempeh-and-japanese-eggplant","kitchen-sink-pasta-recipe","eggplant-and-okra-stew-recipe"]),
("vegetarian-cauliflower-recipes","Cauliflower Recipes: Roasted, Curried, Breaded and in Pasta","Cauliflower as a main course",
 "Vegetarian cauliflower recipes from Herbivoracious: Sichuan spicy cauliflower, Sicilian pasta, roasted cauliflower and white bean salad, gobi masala and more.",
 "Cauliflower is one of the best vegetables for browning, and browning is where the flavor comes from. These recipes roast it, pan-roast it, bread it, curry it and toss it with pasta, including a spicy Sichuan version and a Sicilian spaghetti.",
 ["sichuan-spicy-cauliflower-recipe","sicilian-spaghetti-with-pan-roasted-cauliflower","rigatoni-with-roasted-cauliflower","pappardelle-wit","sephardic-style-breaded-cauliflower","roasted-cauliflower-and-white-bean-salad","gobi-masala-cauliflower-curry-recipe","recipe-roasted","lemon-cream-pasta-with-cauliflower"]),
("vegetarian-thanksgiving-recipes","Vegetarian Thanksgiving Recipes: Sides and Showstoppers","Dishes for a holiday table that does not need a turkey",
 "Vegetarian Thanksgiving recipes from Herbivoracious: vegetarian gravy, brown butter cornbread, roasted green beans, gratin, stuffed squash, bread pudding and more.",
 "A vegetarian Thanksgiving is mostly a matter of making the sides the stars, and a gravy everyone can eat. This collection pulls together the recipes from Herbivoracious that suit a holiday table: vegetarian gravy, cornbread, roasted green beans and Brussels sprouts, gratin, stuffed squash and a savory bread pudding.",
 ["vegetarian-gravy-guess","perfect-pan-roasted-green-beans-recipe","best-cornbread-ever","potato-and-fennel-gratin","crispy-garlicky-smashed-potatoes","savory-bread-pudding-with-morels","recipe-delicata","alices-savory-sweet-life","roasted-cippolini-onions-and-beets","maple-roasted-shiitake-mushrooms-recipe","pan-roasted-brussels-sprouts-with-shiitakes","brusels-sprout-and-apple-hash","warm-fennel-salad-with-pears","tomato-and-beet-salad-recipe"]),
]
for slug,title,sub,desc,intro,rs in H:
    rs=[x for x in (res(r) for r in rs) if x]
    cover=None
    for r in rs:
        m=re.search(r'cover:\s*\n\s*image:\s*"([^"]+)"',open(f'site/content/posts/{r}.md').read())
        if m: cover=m.group(1); break
    fm=f'---\ntitle: "{title}"\nsubtitle: "{sub}"\nslug: "{slug}"\ndescription: "{desc}"\n'
    if cover: fm+=f'cover:\n  image: "{cover}"\n'
    fm+='recipes:\n'+''.join(f'  - "{r}"\n' for r in rs)+'---\n\n'+intro+'\n'
    open(f'site/content/collections/{slug}.md','w').write(fm); print(slug,len(rs))

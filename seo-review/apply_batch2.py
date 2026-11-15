import re,json
P={
"ethiopian-ful-mudammas-recipe":("Ethiopian Ful (Ful Medames) Recipe with Berbere","Ethiopian ful: fava beans simmered with berbere and finished with tasty garnishes. An inexpensive, hearty vegetarian dish for breakfast or dinner."),
"pretzel-ice-cream-recipe":("Pretzel Ice Cream Recipe (Homemade, Salty-Sweet)","Homemade pretzel ice cream with a custard base infused with toasted pretzel flavor, plus crunchy pretzel pieces. A salty-sweet scoop worth the effort."),
"vietnamese-green-mango-salad-recipe":("Vietnamese Green Mango Salad Recipe","A vegetarian Vietnamese green mango salad with bright, bold flavors. Easy to make with a handful of fresh ingredients."),
"kimchi-fried-rice-kimchi-bokkeumbap-recipe":("Kimchi Fried Rice (Kimchi Bokkeumbap) Recipe","Kimchi fried rice, or kimchi bokkeumbap, is a classic Korean way to use up leftover rice. A fast, savory vegetarian version."),
"basic-baked-custard-recipe-an-easy-comforting-dessert-with-many-options":("Easy Baked Custard Recipe (Silky, Never Grainy)","A simple baked custard in ramekins, with the method that keeps it silky instead of grainy. Easy to flavor many ways."),
"kala-chana-black-chickpea-curry":("Kala Chana (Black Chickpea) Curry Recipe","Kala chana, a black chickpea curry, from a guest post by Amee of Rabbit Food Rocks. A hearty Indian vegetarian main."),
"tomato-and-beet-salad-recipe":("Beet and Tomato Salad with Feta and Mint","An easy summer salad of fresh tomatoes and beets with feta and mint. Vegetarian and gluten-free."),
"caramelized-banana-and-buttermilk-panna-cotta-vegetarian-panna-cotta-recipe":("Is Panna Cotta Vegetarian? Banana Panna Cotta Recipe","Traditional panna cotta uses gelatin, so it isn't vegetarian. This caramelized banana and buttermilk version is set with agar instead."),
"indian-lentil-soup-with-fenugreek-or-methi-dal-guest-post-recipe":("Methi Dal: Indian Lentil Soup with Fenugreek","A simple, delicious Indian red lentil soup with fresh fenugreek (methi). Vegetarian, vegan and gluten-free."),
"compressed-cucumber-shiso-sake-infusion":("Compressed Cucumber (and Cantaloupe) with Shiso Sake","How to make compressed cucumber and cantaloupe, and shiso-infused sake, two modern techniques you can do in a home kitchen."),
"kinoko-gohan-japanese-mushroom-rice-recipe":("Japanese Mushroom Rice (Kinoko Gohan) Recipe","Kinoko gohan is classic, soothing Japanese mushroom rice, a fall comfort food that works year round with cultivated mushrooms."),
"red-chili-sauce-for-tamales":("Red Chili Sauce for Tamales Recipe","A red chili sauce for tamales, plus a great tamale book. Make the sauce ahead and use it for fillings or dipping."),
"recipe-syrian-y":("Syrian Red Lentil Soup (Shurbat Addes) Recipe","Syrian red lentil soup (shurbat addes), a vegetarian Aleppo-style recipe adapted from Poopa Dweck's Aromas of Aleppo."),
"quickie-amba-pickled-mango-condiment-recipe":("Quick Amba (Pickled Mango Sauce) Recipe","What is amba? A tangy pickled mango condiment used on sabich and falafel. This quick version needs no fermenting."),
"coconut-rice-with-black-beans-plantains-and-mango-salsa-recipe":("Coconut Rice and Black Beans with Plantains","Caribbean-style coconut rice with black beans, plantains, avocado and mango salsa. A vegetarian entree."),
"homemade-caraway-rye-crackers-recipe":("Homemade Rye Crackers Recipe (Caraway)","Crisp homemade rye crackers with caraway seeds, easy to make and great with cheese or spreads."),
"asparagus-and-tofu-with-guilin-chili-sauce":("Guilin Chili Sauce: Asparagus and Tofu Stir-Fry","A stir-fry of asparagus and tofu with Guilin chili sauce, the garlicky Chinese chili condiment."),
"vegetarian-frijoles-charros-mexican-cowboy-beans-with-smoked-onion-recipe":("Vegetarian Cowboy Beans (Frijoles Charros) Recipe","Vegetarian frijoles charros, Mexican cowboy beans, flavored with smoked onions instead of meat. Vegan-friendly."),
"mandu-koreanstyle-potstickers-with-ssamjang-kochujang-sauce-recipe":("Korean Potstickers (Mandu) with Ssamjang Sauce","Vegetarian Korean-style potstickers (mandu) with an unusual dipping sauce made with ssamjang and kochujang."),
"thai-basil-eggplant-recipe":("Thai Basil Eggplant Recipe (Vegetarian)","Thai basil eggplant, a quick vegetarian stir-fry. Includes how Thai basil differs from holy basil and Italian basil."),
"red-rice-and-avocado-with-crispy-burdock-chips-recipe":("Crispy Burdock (Gobo) Chips Recipe","How to make crispy burdock root (gobo) chips, served here on red rice with avocado."),
"jalapeno-sorghum-butter-recipe":("Sorghum Butter Recipe (Jalapeno) for Cornbread","What is sorghum butter? Butter whipped with sorghum syrup and jalapeno, made for brown butter cornbread."),
"aji-amarillo-hot-sauce-from-peruvian-chile-peppers-recipe":("Aji Amarillo Hot Sauce Recipe","A fruity, spicy hot sauce made from Peruvian aji amarillo chile peppers."),
"vegan-bacon-from-king-oyster-mushrooms-recipe":("Vegan Bacon from King Oyster Mushrooms","Crispy, salty, smoky vegan bacon made from thin-sliced king oyster mushrooms."),
"chanterelle-tostadas-recipes":("Chanterelle Recipes: Chanterelle Tostadas","How to cook chanterelles on crisp tostadas, a simple recipe for wild mushroom season."),
"bocoles-masa-and-black-bean-cakes-with-spicy-yams-recipe":("Bocoles Recipe: Masa and Black Bean Cakes","Bocoles are fried masa cakes stuffed with black beans, here topped with spicy yams."),
"chickpea-cakes-recipe":("Chickpea Cakes Recipe (Pan-Fried, Vegetarian)","Savory pan-fried chickpea cakes flavored with garlic and sesame seeds."),
"potatoes-with-crispy-curry-leaves-recipe":("Crispy Fried Curry Leaves: Potatoes Recipe","How to fry curry leaves until crispy, and a potato dish that shows them off."),
}
for slug,(t,d) in P.items():
    f=f"site/content/posts/{slug}.md"; s=open(f).read()
    head,rest=s.split("\n---\n",1) if s.startswith("---\n") else (None,None)
    q=lambda x:'"'+x.replace('"','\\"')+'"'
    head=re.sub(r'^seo_title:.*\n?','',head,flags=re.M)
    head=re.sub(r'^description:.*\n?','',head,flags=re.M)
    head=re.sub(r'^(title:.*)$',lambda m:m.group(1)+f'\ndescription: {q(d)}\nseo_title: {q(t)}',head,count=1,flags=re.M)
    open(f,'w').write(head+"\n---\n"+rest)
    assert len(t)<=62,(t,len(t)); assert len(d)<=165,(d,len(d))
print(len(P),"updated")

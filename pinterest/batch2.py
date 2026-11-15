import csv, datetime as dt
R = {r['Title']: r for r in csv.DictReader(open('pins.csv'))}
# (index-title, description, keywords)
P = [
("Butternut Squash Soup with Maple Pumpkin Seeds","A vegan, gluten-free butternut squash soup with celery, sage and garlic, finished with crunchy maple-candied pumpkin seeds. Ready in 45 minutes and serves 4 to 6.","butternut squash soup,vegan soup,fall soup recipes,maple pumpkin seeds,gluten free soup"),
("Achiote-Rubbed Butternut Squash Tacos","Butternut squash rubbed with achiote and grilled with poblanos, tossed with crema and cilantro, and piled onto corn tortillas with queso panela. One of the best vegetarian tacos ever.","butternut squash tacos,vegetarian tacos,achiote,grilled squash,fall dinner"),
("Brown Butter Cornbread","Moist, not cakey cornbread with deep corn flavor. Browning the butter first adds the savory depth you would otherwise get from bacon drippings. The best match for a pot of chili.","brown butter cornbread,best cornbread,vegetarian cornbread,chili side dish,thanksgiving side"),
("How To Make Crispy, Delicious Latkes (Jewish Potato Pancakes, Traditional for Hanukkah)","A purist's latke: russet potato, onion, egg and salt, fried until shatteringly crisp. Tips for getting the crunch right, for Hanukkah or any winter brunch.","latkes,potato pancakes,hanukkah recipes,crispy latkes,jewish holiday food"),
("Black Rice Fritters with Chimichurri - a Hanukkah Friendly Entree Recipe","Pan-fried black rice fritters with a crisp edge and chewy center, served with bright parsley chimichurri. A lighter vegetarian entree for Hanukkah after all those latkes.","black rice fritters,hanukkah entree,chimichurri,vegetarian entree,rice fritters"),
("Maple-Roasted Shiitake Mushrooms","Shiitake caps tossed with real maple syrup and roasted until sweet, smoky and savory all at once. An easy side dish that works for holiday tables.","roasted shiitake,maple mushrooms,mushroom side dish,thanksgiving side dish,vegetarian sides"),
("Alice's Savory Sweet Life Cookbook - And Her Recipe for Roasted Carrots with Sage Brown Butter","Roasted carrots finished with sage brown butter, from Alice Currah's Savory Sweet Life cookbook. A simple, beautiful vegetable side for fall and winter dinners.","roasted carrots,sage brown butter,carrot side dish,thanksgiving vegetables,fall sides"),
("Roasted Cippolini Onions and Beets","Cippolini onions and beets roasted together with red wine vinegar and a little sugar until sweet and tangy. An easy make-ahead side for the holidays.","roasted beets,cipollini onions,roasted vegetables,holiday side dish,make ahead sides"),
("White Bean and Kale Soup","A hearty white bean and kale soup with rosemary, a whole head of garlic and a parmesan rind or dried porcini for depth. Pressure-cooker friendly; vegan option and gluten-free.","white bean and kale soup,vegetarian soup,pressure cooker beans,cannellini soup,winter soup"),
("Spanish Lentil and Mushroom Stew","Thick-cut browned mushrooms and French green lentils, seasoned with sherry vinegar and smoked paprika. A chewy, deeply savory vegetarian stew with a Spanish accent.","lentil stew,mushroom stew,vegetarian stew,smoked paprika,hearty vegetarian"),
("Chili Borracho","Bean-forward vegetarian chili with dark beer, dried chiles and unsweetened cocoa for mole-like depth, made from scratch in the pressure cooker and topped with plenty of garnishes.","vegetarian chili,bean chili,chili borracho,pressure cooker chili,game day food"),
("Triple-Smoky Mac and Cheese","Grown-up mac and cheese with smoked cheddar, smoked paprika and chipotle. Make it ahead for dinner parties and add the breadcrumb topping at the last minute.","smoky mac and cheese,vegetarian mac and cheese,make ahead mac and cheese,smoked cheddar,comfort food"),
("Chocolate-Chunk Bread Pudding","A custard-rich bread pudding made with leftover challah or brioche and molten chunks of bittersweet chocolate. A cozy winter dessert that uses up day-old bread.","chocolate bread pudding,challah bread pudding,winter desserts,bread pudding recipe,leftover bread"),
("Apple Crostata with Breadcrumb Streusel","A fuss-free apple pie made on a sheet pan, with a crisp breadcrumb streusel. No crimped crust or lattice required, and it feeds a crowd.","apple crostata,easy apple pie,apple dessert,thanksgiving dessert,rustic tart"),
("Spectacular Chocolate-Espresso Brownies","Dense, very moist cakey brownies with a double dose of salt, better chocolate and espresso. Adapted from a classic and simplified to use one less bowl.","chocolate espresso brownies,best brownies,cakey brownies,brownie recipe,chocolate dessert"),
("Seckel Pears with Cinnamon Pastry Crumbs","Peeled Seckel pears poached in pear brandy and served with buttery cinnamon pastry crumbs and vanilla ice cream. An elegant fall dessert.","seckel pears,poached pears,pear dessert,fall dessert,elegant dessert"),
("Basic Baked Custard","A simple baked custard in ramekins, and the method that keeps it silky instead of grainy. Every cook should have this easy, comforting dessert in their repertoire.","baked custard,easy dessert,ramekin desserts,custard recipe,classic dessert"),
("Pear and Gouda Salad","Crisp pear and aged gouda with fresh ginger and quick cryo-pickled onions, dressed with a vinaigrette made from the pickling liquid. A great fall or holiday salad.","pear salad,gouda salad,fall salad,holiday salad,cheese salad"),
("Caramelized Apple and Blue Cheese Crostini","Deeply caramelized crisp apples, blue cheese and tarragon oil on toasted bread. An easy appetizer that surprises guests with big flavor.","apple crostini,blue cheese appetizer,holiday appetizer,party appetizer,caramelized apples"),
("Cheddar and Apple Butter Panini with Rosemary Candied Pecans - Guest Recipe from Kathy Strahs of Panini Happy","A panini with sharp cheddar, apple butter and rosemary candied pecans for sweet, salty crunch. Guest recipe from Kathy Strahs of Panini Happy.","apple butter panini,cheddar sandwich,vegetarian sandwich,candied pecans,grilled cheese ideas"),
("Gougères - Cheesy Puffs of Goodness with Blue Cheese and Rosemary","Airy cheese puffs made from simple choux paste with blue cheese and rosemary, and no yeast or baking powder needed. A classic French party snack.","gougeres,cheese puffs,choux pastry,party appetizer,holiday appetizers"),
("Couscous with Parsley Yogurt Sauce, Spicy Acorn Squash, Roasted Cauliflower and Chickpeas","Couscous topped with spicy roasted acorn squash, cauliflower and chickpeas, with a bright parsley yogurt sauce. A colorful vegetarian dinner for fall.","acorn squash recipe,couscous bowl,roasted cauliflower,chickpea dinner,vegetarian dinner"),
("Pozole Rojo de Frijol","A vegetarian pozole with hominy and beans in a mildly spicy, sour red chile broth. A hearty one-pot meal for cold days.","vegetarian pozole,pozole rojo,hominy soup,mexican soup,one pot meal"),
("Mujadara – Middle Eastern Rice and Lentil Pilaf","Rice and lentils with cumin, cinnamon and a big pile of caramelized onions. Inexpensive, satisfying and best served near room temperature with Greek yogurt.","mujadara,lentil rice pilaf,middle eastern recipes,caramelized onions,budget vegetarian"),
("Kimchi Stew (Kimchi Jigae) with Shiitake and Daikon","Classic Korean kimchi jigae with shiitake, daikon and tofu, spiked with gochujang and miso. Simple enough for a weeknight and easy to adapt.","kimchi jigae,kimchi stew,korean stew,vegetarian korean,gochujang"),
("Kinoko Gohan (Japanese Mushroom Rice)","Japanese mushroom rice, a soothing fall comfort food made with a mix of mushrooms. Works year round with cultivated mushrooms.","kinoko gohan,japanese mushroom rice,mushroom rice,japanese comfort food,rice recipes"),
("Kasha Pilaf with Dates, Pistachios and Baharat","Nutty toasted buckwheat kasha with sweet dates, pistachios and warm baharat spice. A satisfying pilaf that also makes a great stuffing.","kasha pilaf,buckwheat recipes,baharat,grain side dish,dates and pistachios"),
("Caramelized Pear and Ginger Scones","Buttery buttermilk scones studded with caramelized pear and fresh ginger, finished with a sugar topping. A cozy fall baking project.","pear scones,ginger scones,fall baking,scone recipe,breakfast baking"),
]
rows=[]
start=dt.datetime(2026,11,16,18,0)   # 18:00 UTC = 10 AM PST; second slot of each day at 01:00 UTC next day = 5 PM PST
slots=[]
for d in range(14):
    base=start+dt.timedelta(days=d)
    slots += [base, base+dt.timedelta(hours=7)]
for i,(t,desc,kw) in enumerate(P):
    r=next(v for k,v in R.items() if k[:60]==t[:60]); t=r["Title"]
    assert len(t)<=100 or True
    rows.append({"Title":t[:100],"Media URL":r["Media URL"],"Pinterest board":r["Pinterest board"],"Thumbnail":"","Description":desc,"Link":r["Link"],"Publish date":slots[i].strftime("%Y-%m-%dT%H:%M:%S"),"Keywords":kw})
# interleave boards: simple sort by slot already mixed; print summary
with open('batch2.csv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=["Title","Media URL","Pinterest board","Thumbnail","Description","Link","Publish date","Keywords"]); w.writeheader(); w.writerows(rows)
print(len(rows)); 
for r in rows: print(r["Publish date"],r["Pinterest board"][:18],r["Title"][:50])

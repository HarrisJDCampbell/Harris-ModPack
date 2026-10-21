package dev.harriscampbell.harris;

import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.food.FoodProperties;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.Rarity;
import net.neoforged.neoforge.registries.DeferredItem;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModItems {
    public static final DeferredRegister.Items ITEMS = DeferredRegister.createItems(HarrisMod.MODID);

    /** Mum's shepherd's pie: the best food in the game, and it isn't close. */
    public static final DeferredItem<Item> MUMS_SHEPHERDS_PIE = ITEMS.register("mums_shepherds_pie",
            () -> new ShepherdsPieItem(new Item.Properties()
                    .stacksTo(16)
                    .rarity(Rarity.UNCOMMON)
                    .food(new FoodProperties.Builder()
                            .nutrition(14)
                            .saturationModifier(1.0f)
                            .usingConvertsTo(Items.BOWL)
                            .effect(() -> new MobEffectInstance(MobEffects.REGENERATION, 20 * 20, 0), 1.0f)
                            .effect(() -> new MobEffectInstance(MobEffects.ABSORPTION, 20 * 120, 1), 1.0f)
                            .build())));

    private ModItems() {}
}

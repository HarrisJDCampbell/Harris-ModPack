package dev.harriscampbell.harris;

import com.mojang.logging.LogUtils;
import net.minecraft.world.item.CreativeModeTabs;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;
import org.slf4j.Logger;

/**
 * Harris ModPack's own mod: the funny stuff that needs real code.
 *
 * Two event buses matter in NeoForge:
 *  - the mod bus (passed into this constructor) fires once during startup:
 *    registries, creative tabs, client setup;
 *  - NeoForge.EVENT_BUS fires during gameplay: explosions, ticks, players.
 */
@Mod(HarrisMod.MODID)
public final class HarrisMod {
    public static final String MODID = "harris";
    public static final Logger LOGGER = LogUtils.getLogger();

    public HarrisMod(IEventBus modBus, ModContainer container) {
        ModItems.ITEMS.register(modBus);

        modBus.addListener(HarrisMod::addToCreativeTabs);
    }

    private static void addToCreativeTabs(BuildCreativeModeTabContentsEvent event) {
        if (event.getTabKey() == CreativeModeTabs.FOOD_AND_DRINKS) {
            event.accept(ModItems.MUMS_SHEPHERDS_PIE);
        }
    }
}

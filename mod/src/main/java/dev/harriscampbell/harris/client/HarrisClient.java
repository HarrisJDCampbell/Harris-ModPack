package dev.harriscampbell.harris.client;

import dev.harriscampbell.harris.HarrisMod;
import dev.harriscampbell.harris.ModParticles;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.fml.ModContainer;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.client.event.RegisterParticleProvidersEvent;
import net.neoforged.neoforge.client.gui.ConfigurationScreen;
import net.neoforged.neoforge.client.gui.IConfigScreenFactory;

/** Client-only half of the mod. Never loaded on a dedicated server. */
@Mod(value = HarrisMod.MODID, dist = Dist.CLIENT)
public final class HarrisClient {
    public HarrisClient(IEventBus modBus, ModContainer container) {
        modBus.addListener(HarrisClient::registerParticles);
        // Mods menu > Harris > Config edits harris-common.toml in-game.
        container.registerExtensionPoint(IConfigScreenFactory.class, ConfigurationScreen::new);
    }

    private static void registerParticles(RegisterParticleProvidersEvent event) {
        event.registerSpriteSet(ModParticles.CONFETTI.get(), ConfettiParticle.Provider::new);
    }
}

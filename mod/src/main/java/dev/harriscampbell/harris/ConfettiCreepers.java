package dev.harriscampbell.harris;

import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.monster.Creeper;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.event.level.ExplosionEvent;

/**
 * Creepers still hiss, swell and "explode", but the explosion is cancelled and
 * replaced with a confetti burst and party sounds.
 *
 * ExplosionEvent.Start fires server-side before any blocks or entities are
 * touched, so cancelling it is enough: no crater, no damage, no knockback.
 * The creeper still removes itself afterwards, exactly like a normal explosion.
 */
public final class ConfettiCreepers {
    private static final ResourceLocation SURPRISE_PARTY =
            ResourceLocation.fromNamespaceAndPath(HarrisMod.MODID, "surprise_party");

    static void onExplosionStart(ExplosionEvent.Start event) {
        if (!HarrisConfig.CONFETTI_CREEPERS.get()) return;
        if (!(event.getExplosion().getDirectSourceEntity() instanceof Creeper creeper)) return;
        if (!(event.getLevel() instanceof ServerLevel level)) return;

        event.setCanceled(true);
        Vec3 pos = creeper.position();
        int amount = HarrisConfig.CONFETTI_AMOUNT.get() * (creeper.isPowered() ? 2 : 1);

        // One packet: each client spawns `amount` particles with a random spread
        // and random velocities scaled by the last argument.
        level.sendParticles(ModParticles.CONFETTI.get(),
                pos.x, pos.y + 1.0, pos.z, amount, 0.4, 0.6, 0.4, 0.45);

        level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.FIREWORK_ROCKET_LARGE_BLAST, SoundSource.HOSTILE, 2.0f, 1.0f);
        level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.FIREWORK_ROCKET_TWINKLE, SoundSource.HOSTILE, 1.5f, 1.0f);
        level.playSound(null, pos.x, pos.y, pos.z, SoundEvents.VILLAGER_CELEBRATE, SoundSource.HOSTILE, 1.5f, 1.3f);

        AdvancementHolder advancement = level.getServer().getAdvancements().get(SURPRISE_PARTY);
        if (advancement != null) {
            for (ServerPlayer player : level.getPlayers(p -> p.distanceToSqr(pos) < 12 * 12)) {
                player.getAdvancements().award(advancement, "party");
            }
        }
    }

    private ConfettiCreepers() {}
}

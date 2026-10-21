package dev.harriscampbell.harris;

import net.minecraft.core.particles.ParticleType;
import net.minecraft.core.particles.SimpleParticleType;
import net.minecraft.core.registries.Registries;
import net.neoforged.neoforge.registries.DeferredHolder;
import net.neoforged.neoforge.registries.DeferredRegister;

public final class ModParticles {
    public static final DeferredRegister<ParticleType<?>> PARTICLE_TYPES =
            DeferredRegister.create(Registries.PARTICLE_TYPE, HarrisMod.MODID);

    // overrideLimiter=true: confetti is spawned in big bursts, don't let the
    // client's particle cap thin it out.
    public static final DeferredHolder<ParticleType<?>, SimpleParticleType> CONFETTI =
            PARTICLE_TYPES.register("confetti", () -> new SimpleParticleType(true));

    private ModParticles() {}
}

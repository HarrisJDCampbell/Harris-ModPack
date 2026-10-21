package dev.harriscampbell.harris.client;

import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.particle.Particle;
import net.minecraft.client.particle.ParticleProvider;
import net.minecraft.client.particle.ParticleRenderType;
import net.minecraft.client.particle.SpriteSet;
import net.minecraft.client.particle.TextureSheetParticle;
import net.minecraft.core.particles.SimpleParticleType;

/**
 * A scrap of confetti: white sprite tinted a party colour, launched outward,
 * then it slows down, spins, wobbles and drifts to the ground.
 */
public class ConfettiParticle extends TextureSheetParticle {
    private static final float[][] COLOURS = {
            {0.98f, 0.27f, 0.36f}, // red
            {1.00f, 0.62f, 0.16f}, // orange
            {1.00f, 0.86f, 0.20f}, // yellow
            {0.36f, 0.85f, 0.42f}, // green
            {0.25f, 0.68f, 1.00f}, // blue
            {0.66f, 0.42f, 1.00f}, // purple
            {1.00f, 0.45f, 0.78f}, // pink
            {1.00f, 1.00f, 1.00f}, // white
    };

    private final float spin;

    protected ConfettiParticle(ClientLevel level, double x, double y, double z,
                               double vx, double vy, double vz, SpriteSet sprites) {
        super(level, x, y, z);
        this.xd = vx;
        this.yd = vy + 0.12 + this.random.nextFloat() * 0.18; // little upward pop
        this.zd = vz;
        this.pickSprite(sprites);
        float[] c = COLOURS[this.random.nextInt(COLOURS.length)];
        this.setColor(c[0], c[1], c[2]);
        this.quadSize = 0.06f + this.random.nextFloat() * 0.06f;
        this.lifetime = 80 + this.random.nextInt(80);
        this.gravity = 0.35f;
        this.friction = 0.90f;
        this.spin = (this.random.nextFloat() - 0.5f) * 0.5f;
        this.roll = this.random.nextFloat() * (float) Math.PI * 2;
        this.oRoll = this.roll;
    }

    @Override
    public void tick() {
        this.oRoll = this.roll;
        super.tick();
        if (!this.onGround) {
            this.roll += this.spin;
            // flutter: tiny random sideways drift so it doesn't fall like a rock
            this.xd += (this.random.nextFloat() - 0.5f) * 0.012f;
            this.zd += (this.random.nextFloat() - 0.5f) * 0.012f;
        }
    }

    @Override
    public ParticleRenderType getRenderType() {
        return ParticleRenderType.PARTICLE_SHEET_OPAQUE;
    }

    public record Provider(SpriteSet sprites) implements ParticleProvider<SimpleParticleType> {
        @Override
        public Particle createParticle(SimpleParticleType type, ClientLevel level, double x, double y, double z,
                                       double vx, double vy, double vz) {
            return new ConfettiParticle(level, x, y, z, vx, vy, vz, this.sprites);
        }
    }
}
